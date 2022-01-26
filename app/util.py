"""Utilities."""
import asyncio
import copy
import json
import logging
from pathlib import Path
import traceback
from typing import Any, Optional

import httpx
import pydantic
from reasoner_pydantic import Response

EXAMPLES_DIR = Path(__file__).parent / "openapi_examples"


async def post_safely(
    url: str,
    payload: Any,
    client: Optional[httpx.AsyncClient] = None,
    **kwargs,
):
    """POST a json payload to url."""
    if client is None:
        async with httpx.AsyncClient() as client:
            return await _post_safely(client, url, payload, **kwargs)

    return await _post_safely(client, url, payload, **kwargs)


async def _post_safely(
    client: httpx.AsyncClient,
    url: str,
    payload: Any,
    timeout: Optional[float] = None,
    logger: Optional[logging.Logger] = None,
    service_name: Optional[str] = None,
):
    if not logger:
        logger = logging.getLogger(__name__)
    if not service_name:
        service_name = url
    try:
        # use waitfor instead of httpx's timeout because: https://github.com/encode/httpx/issues/1451#issuecomment-907400740
        response = await client.post(
                url,
                json=payload,
            )
        response.raise_for_status()
        response_json = response.json()
        Response(**response_json)  # validate against TRAPI
        return response_json
    except asyncio.TimeoutError as e:
        logger.warning({
            "message": f"{service_name} took >{timeout} seconds to respond",
            "error": str(e),
            "request": {
                "url": url,
                "data": elide_curies(payload),
            },
        })
    except httpx.RequestError as e:
        # Log error
        logger.warning({
            "message": f"Error contacting {service_name}",
            "error": str(e),
            "request": log_request(e.request),
        })
    except httpx.HTTPStatusError as e:
        # Log error with response
        logger.warning({
            "message": f"Error response from {service_name}",
            "error": str(e),
            "request": log_request(e.request),
            "response": log_response(e.response),
        })
    except json.JSONDecodeError as e:
        # Log error with response
        logger.warning({
            "message": f"Received bad JSON data from {service_name}",
            "request": {
                "data": payload,
            },
            "response": {
                "data": e.doc
            },
            "error": str(e),
        })
    except pydantic.ValidationError as e:
        logger.warning({
            "message": f"Received non-TRAPI compliant response from {service_name}",
            "error": str(e),
        })
    except Exception as e:
        traceback.print_exc()
        logger.warning({
            "message": f"Something went wrong while querying {service_name}",
            "error": str(e),
        })
    raise RuntimeError(f"Failed to get a good response from {service_name}, see the logs")


def elide_curies(payload):
    """Elide CURIES in TRAPI request/response."""
    payload = copy.deepcopy(payload)
    if "message" not in payload:
        return payload
    for qnode in payload["message"]["query_graph"]["nodes"].values():
        if (num_curies := len(qnode.get("ids", None) or [])) > 10:
            qnode["ids"] = f"**{num_curies} CURIEs not shown for brevity**"
    return payload


def log_request(r):
    """Serialize a httpx.Request object into a dict for logging."""
    data = r.read().decode()
    # the request body can be cleared out by httpx under some circumstances
    # let's not crash if that happens
    try:
        data = elide_curies(json.loads(data))
    except Exception:
        pass
    return {
        "method" : r.method,
        "url" : str(r.url),
        "headers" : dict(r.headers),
        "data" : data
    }


def log_response(r):
    """Serialize a httpx.Response object into a dict for logging."""
    return {
        "status_code" : r.status_code,
        "headers" : dict(r.headers),
        "data" : r.text,
    }


def load_example(name):
    """Load example from JSON file."""
    with open(EXAMPLES_DIR / (name + ".json"), "r") as stream:
        return json.load(stream)


def drop_nulls(obj):
    """Recursively remove null-valued properties."""
    if isinstance(obj, list):
        return [
            drop_nulls(el) for el in obj
        ]
    if isinstance(obj, dict):
        return {
            key: drop_nulls(value)
            for key, value in obj.items()
            if value is not None
        }
    return obj
