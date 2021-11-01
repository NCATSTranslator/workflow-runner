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
    version="1.2.0",
    terms_of_service="",
    translator_component="ARA",
    translator_teams=["Standards Reference Implementation Team"],
    contact={
        "name": "Kenny Morton",
        "email": "kenny@covar.com",
        "x-id": "kennethmorton",
        "x-role": "responsible developer",
    },
)
OPENAPI_SERVER_URL = os.getenv("OPENAPI_SERVER_URL")
OPENAPI_SERVER_MATURITY = os.getenv("OPENAPI_SERVER_MATURITY", "development")
if OPENAPI_SERVER_URL:
    openapi_args["servers"] = [
        {
            "url": OPENAPI_SERVER_URL,
            "x-maturity": OPENAPI_SERVER_MATURITY,
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
        LOGGER.warning("Invalid URL '%s': %s", endpoint["url"], err)
        continue
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
