"""Workflow runner."""
from app.models import Services
from collections import defaultdict
import logging

from fastapi import Body
import httpx
from reasoner_pydantic import Query as ReasonerQuery, Response

from .util import load_example, drop_nulls
from .trapi import TRAPI
from .smartapi import SmartAPI

LOGGER = logging.getLogger(__name__)
APP = TRAPI(
    title="Workflow runner",
    version="1.0.0",
    terms_of_service="",
    translator_component="ARA",
    translator_teams=["SRI"],
    contact={
        "name": "Patrick Wang",
        "email": "patrick@covar.com",
        "x-id": "patrickkwang",
        "x-role": "responsible developer",
    },
)

endpoints = SmartAPI().get_operations_endpoints()
SERVICES = defaultdict(list)
for endpoint in endpoints:
    for operation in endpoint["operations"]:
        SERVICES[operation].append(endpoint["url"] + "/query")
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
    async with httpx.AsyncClient() as client:
        for operation in workflow:
            url = SERVICES[operation["id"]][0]  # just take the first one
            LOGGER.debug(f"POSTing operation '{operation}' to {url}...")
            response = await client.post(
                url,
                json={
                    "message": message,
                    "workflow": [
                        operation,
                    ],
                },
                timeout=30.0,
            )
            if response.status_code > 200:
                raise ValueError(str(response.status_code) + ": " + response.text)
            message = drop_nulls(response.json()["message"])
    return Response(
        message=message,
        workflow=workflow,
    )


@APP.get(
    "/services",
    # response_model=Services,
)
async def get_services() -> Services:
    """Get registered services."""
    return SERVICES
