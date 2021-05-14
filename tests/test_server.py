"""Test server."""
import json
from pathlib import Path

from fastapi import testclient
from fastapi.testclient import TestClient

from app.server import APP

testclient = TestClient(APP)

THIS_DIR = Path(__file__).parent
EXAMPLE_DIR = THIS_DIR.parent / "app" / "openapi_examples"

with open(EXAMPLE_DIR / "query.json") as stream:
    REQUEST = json.load(stream)
with open(EXAMPLE_DIR / "response.json") as stream:
    RESPONSE = json.load(stream)


def drop_nulls(obj):
    """Recursively remove null-valued properties."""
    if not isinstance(obj, dict):
        return obj
    return {
        key: drop_nulls(value)
        for key, value in obj.items()
        if value is not None
    }


def test_query():
    """Test calling /query endpoint."""
    response = testclient.post(
        "/query",
        json=REQUEST,
    )
    response.raise_for_status()
    assert drop_nulls(response.json()) == RESPONSE


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
