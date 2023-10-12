"""Workflow runner."""
from app.models import Services, Operations
from collections import defaultdict
import logging
import os

from fastapi import Body
import httpx
from pydantic import HttpUrl, ValidationError
from pydantic.tools import parse_obj_as
from reasoner_pydantic import Query as ReasonerQuery, Response
from reasoner_pydantic import Message, QueryGraph, KnowledgeGraph, Results, AuxiliaryGraphs
from starlette.middleware.cors import CORSMiddleware

from .wfr_logging import gen_logger
from .util import load_example, drop_nulls, post_safely
from .trapi import TRAPI
from .smartapi import SmartAPI
from .standard_operations import StandardOperations

LOGGER = logging.getLogger(__name__)

openapi_args = dict(
    title="Workflow runner",
    version="1.6.6",
    terms_of_service="",
    translator_component="ARA",
    translator_teams=["Standards Reference Implementation Team"],
    infores="infores:workflow-runner",
    contact={
        "name": "Abrar Mesbah",
        "email": "amesbah@covar.com",
        "x-id": "uhbrar",
        "x-role": "responsible developer",
    },
)
NORMALIZER_URL = os.getenv("NORMALIZER_URL", "https://nodenormalization-sri.renci.org")
OPENAPI_SERVER_URL = os.getenv("OPENAPI_SERVER_URL")
OPENAPI_SERVER_MATURITY = os.getenv("OPENAPI_SERVER_MATURITY", "development")
OPENAPI_SERVER_LOCATION = os.getenv("OPENAPI_SERVER_LOCATION", "RENCI")
TRAPI_VERSION = os.getenv("TRAPI_VERSION", "1.4.0")

if OPENAPI_SERVER_URL:
    openapi_args["servers"] = [
        {
            "url": OPENAPI_SERVER_URL,
            "x-maturity": OPENAPI_SERVER_MATURITY,
            "x-location": OPENAPI_SERVER_LOCATION,
        },
    ]

openapi_args["trapi"] = TRAPI_VERSION

APP = TRAPI(**openapi_args)

APP.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services dict.
# It is set on app startup and on POST /refresh through a global reference.
SERVICES = defaultdict(list)

# Global operations
OPERATIONS = defaultdict(dict)

@APP.post(
        "/query",
        tags=["trapi"],
        response_model=Response,
        response_model_exclude_unset=True,
        responses={
            200: {
                "content": {
                    "application/json": {
                        "example": load_example("response")
                    }
                },
            },
        },
)
async def run_workflow(
        request: ReasonerQuery = Body(..., example=load_example("query")),
) -> Response:
    """Run workflow."""
    request_dict = request.dict(
        exclude_unset=True,
    )
    
    message = request_dict["message"]
    qgraph = message["query_graph"]
    message["auxiliary_graphs"] = message.get("auxiliary_graphs") or {}
    workflow = request_dict["workflow"]
    logger = gen_logger()
    log_level = request_dict.get("log_level", "ERROR")
    logger.setLevel(logging._nameToLevel[log_level])
    completed_workflow = []

    for operation in workflow:
        operation_services = []
        runner_parameters = operation.pop("runner_parameters", {})
        operation_timeout = runner_parameters.get("timeout", 60.0)
        async with httpx.AsyncClient(verify=False, timeout=operation_timeout) as client:
            if "allowlist" in runner_parameters.keys():
                for service in SERVICES.get(operation["id"], []):
                    if service["infores"] in runner_parameters["allowlist"]:
                        operation_services.append(service)
            else:
                for service in SERVICES.get(operation["id"], []):
                    operation_services.append(service)
                if "denylist" in runner_parameters.keys():
                    for service in operation_services:
                        if service["infores"] in runner_parameters["denylist"]:
                            operation_services.remove(service)

            if operation_services:
                logger.debug(f"Service providers to query for operation '{operation}':'{operation_services}'")
            else:
                logger.error(f"Unable to complete workflow: No service providers for operation '{operation}'")
                return Response(
                    message=message,
                    workflow=completed_workflow,
                    logs=logger.handlers[0].store,
                )

            service_operation_responses = []

            for service in operation_services:
                url = service["url"]
                service_name = service["title"]
                logger.debug(f"Requesting operation '{operation}' from {service_name}...")
                try:
                    response = await post_safely(
                        url,
                        {
                            "message": message,
                            "workflow": [
                                operation,
                            ],
                            "submitter": "Workflow Runner",
                        },
                        client=client,
                        timeout=operation_timeout,
                        logger=logger,
                        service_name=service_name,
                    )
                    logger.debug(f"Received operation '{operation}' from {service_name}...")

                    try:
                        response = await post_safely(
                            NORMALIZER_URL + "/query",
                            {
                                "message": response["message"],
                                "submitter": "Workflow Runner"
                            },
                            client=client,
                            timeout=60.0,
                            logger=logger,
                            service_name="node_normalizer"
                        )
                    except RuntimeError as e:
                        logger.warning({
                            "error": str(e)
                        })

                    service_operation_responses.append(response)
                
                except RuntimeError as e:
                    logger.warning({
                        "error": str(e)
                    })

                if not OPERATIONS[operation["id"]]["unique"] and len(service_operation_responses) == 1:
                    # We only need one successful response for non-unique operations
                    break
            
            logger.debug(f"Merging {len(service_operation_responses)} responses for '{operation}'...")
            m = Message(query_graph=QueryGraph.parse_obj(qgraph))
            for response in service_operation_responses:
                response["message"]["query_graph"] = qgraph
                m.update(Message.parse_obj(response["message"]))
            message = m.dict()

            operation["runner_parameters"] = runner_parameters

            completed_workflow.append(operation)
        
    return Response(
        message=message,
        workflow=workflow,
        logs=logger.handlers[0].store,
    )


@APP.get(
    "/services",
    response_model=Services,
)
async def get_services() -> Services:
    """Get registered services."""
    return SERVICES

@APP.get(
    "/operations",
    response_model=Operations,
)
async def get_operations() -> Operations:
    """Get available operations."""
    return OPERATIONS

@APP.on_event("startup")
@APP.post("/refresh")
async def refresh_services_and_operations():
    """Fetch available services from smartapi and operations from standards.ncats.io"""
    global SERVICES
    # Start with empty SERVICES dict.
    SERVICES = defaultdict(list)
    endpoints = SmartAPI(OPENAPI_SERVER_MATURITY, TRAPI_VERSION, LOGGER).get_operations_endpoints()
    for endpoint in endpoints:
        try:
            base_url = parse_obj_as(HttpUrl, endpoint["url"])
        except ValidationError as err:
            # It may contain a relative path
            # This is aloud by smart-api
            # And is relative to the source_url for the open-api doc
            # https://spec.openapis.org/oas/latest.html#server-object
            #
            # The url can also reference variables in {brackets}
            # This is not yet supported here
            try:
                source_url_stem = endpoint["source_url"][:endpoint["source_url"].rfind("/")]
                full_url = source_url_stem + endpoint["url"]
                base_url = parse_obj_as(HttpUrl, full_url)
            except ValidationError as err:
                LOGGER.warning("Invalid URL '%s' '%s': %s", endpoint["source_url"], endpoint["url"], err)
                continue
        # Now actualy check if we can contact the endpoint
        try:
            response = httpx.get(base_url + "/query", follow_redirects=True)
        except (httpx.ReadTimeout, httpx.ConnectError, httpx.ConnectTimeout):
            LOGGER.warning("Discarding '%s due to timeout.", base_url)
            continue
        if response.status_code == 404:
            # Not a valid URL
            try:
                response = httpx.post(base_url + "/query")
            except (httpx.ReadTimeout, httpx.ConnectError, httpx.ConnectTimeout):
                LOGGER.warning("Discarding '%s due to timeout after 404.", base_url)
                continue
            if response.status_code == 404:
                LOGGER.warning("404 recieved for '%s'", base_url)
                continue
        # More than likely this is a 405 or some other error
        # Any response at this point is good

        endpoint["url"] = base_url + "/query"

        # Popped for cleanliness in /services enpoint
        operations = endpoint.pop("operations")
        for operation in operations:
            SERVICES[operation].append(endpoint)
    SERVICES = dict(SERVICES)

    # Update Operations
    global OPERATIONS
    OPERATIONS = StandardOperations().get_operations()

    return "Workflow services and operations refreshed successfully."
