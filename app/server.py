"""Workflow runner."""
from fastapi import Body
from reasoner_pydantic import Query as ReasonerQuery, Response

from .util import load_example
from .trapi import TRAPI

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
    request_dict = request.dict()
    message = request_dict["message"]
    workflow = request_dict["workflow"]
    return Response(
        message=message,
        workflow=workflow,
    )
