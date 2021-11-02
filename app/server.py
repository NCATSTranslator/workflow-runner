"""Workflow runner."""
from app.models import Services
from collections import defaultdict
import logging
import os

from fastapi import Body
import httpx
from pydantic import HttpUrl, ValidationError
from pydantic.tools import parse_obj_as
from reasoner_pydantic import Query as ReasonerQuery, Response
from starlette.middleware.cors import CORSMiddleware

from .logging import gen_logger
from .util import load_example, drop_nulls, post_safely
from .trapi import TRAPI
from .smartapi import SmartAPI

LOGGER = logging.getLogger(__name__)

openapi_args = dict(
    title="Workflow runner",
    version="1.3.0",
    terms_of_service="",
    translator_component="ARA",
    translator_teams=["Standards Reference Implementation Team"],
    infores="infores:workflow-runner",
    contact={
        "name": "Kenny Morton",
        "email": "kenny@covar.com",
        "x-id": "kennethmorton",
        "x-role": "responsible developer",
    },
)
OPENAPI_SERVER_URL = os.getenv("OPENAPI_SERVER_URL")
OPENAPI_SERVER_MATURITY = os.getenv("OPENAPI_SERVER_MATURITY", "development")
OPENAPI_SERVER_LOCATION = os.getenv("OPENAPI_SERVER_LOCATION", "RENCI")
if OPENAPI_SERVER_URL:
    openapi_args["servers"] = [
        {
            "url": OPENAPI_SERVER_URL,
            "x-maturity": OPENAPI_SERVER_MATURITY,
            "x-location": OPENAPI_SERVER_LOCATION,
        },
    ]

APP = TRAPI(**openapi_args)

APP.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

endpoints = SmartAPI().get_operations_endpoints()
SERVICES = defaultdict(list)
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
    response = httpx.get(base_url + "/query")
    if response.status_code == 404:
        # Not a valid URL
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
    workflow = request_dict["workflow"]
    logger = gen_logger()
    async with httpx.AsyncClient() as client:
        for operation in workflow:
            service = SERVICES[operation["id"]][0]  # just take the first one
            url = service["url"]
            service_name = service["title"]
            logger.debug(f"Requesting operation '{operation}' from {service_name}...")
            response = await post_safely(
                url,
                {
                    "message": message,
                    "workflow": [
                        operation,
                    ],
                },
                client=client,
                timeout=30.0,
                logger=logger,
                service_name=service_name,
            )
            logger.debug(f"Received operation '{operation}' from {service_name}...")
            message = drop_nulls(response["message"])
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
