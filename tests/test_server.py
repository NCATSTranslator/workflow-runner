"""Test server."""
import json
from pathlib import Path

from fastapi import testclient
from fastapi.testclient import TestClient

from app.server import APP
from app.util import drop_nulls

testclient = TestClient(APP)

THIS_DIR = Path(__file__).parent
EXAMPLE_DIR = THIS_DIR.parent / "app" / "openapi_examples"

with open(EXAMPLE_DIR / "query.json") as stream:
    REQUEST = json.load(stream)
with open(EXAMPLE_DIR / "response.json") as stream:
    RESPONSE = json.load(stream)


def test_query():
    """Test calling /query endpoint."""
    response = testclient.post("/refresh")
    response = testclient.post(
        "/query",
        json=REQUEST,
    )
    response.raise_for_status()
    response_json = response.json()
    assert len(response_json["message"]["results"]) == 1

def test_services():
    """Test calling /services endpoint."""
    response = testclient.get("/services")
    response.raise_for_status()
    response_json = response.json()

    # The response here should be a dict
    # where keys are operations and values
    # are a list of urls.
    # This is a basic check
    # We could go deeper and look for urls

    assert isinstance(response_json, dict)


def test_endpoint():
    """Test getting OpenAPI."""
    response = testclient.get(
        "/openapi.json",
    )
    response.raise_for_status()
    # and again, to make sure the caching works
    response = testclient.get(
        "/openapi.json",
    )
    response.raise_for_status()
