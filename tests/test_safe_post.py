"""Test safe posting."""
import asyncio
import logging

import fastapi
import httpx
import pytest
from starlette.responses import Response

from app.util import post_safely
from app.logging import gen_logger

mock_app = fastapi.FastAPI()


@mock_app.post("/slow")
async def handle_slow():
    await asyncio.sleep(3)


@mock_app.post("/noncompliant")
async def handle_noncompliant():
    return {}


@mock_app.post("/nonjson")
async def handle_nonjson():
    return Response("this is not JSON")


@pytest.mark.asyncio
async def test_post_safely():
    """Test post_safely()."""
    logger = gen_logger(level=logging.DEBUG)
    logs = logger.handlers[0].store

    async with httpx.AsyncClient(app=mock_app, base_url="http://test") as client:
        with pytest.raises(RuntimeError):
            await post_safely(
                "http://test/slow",
                {},
                client=client,
                timeout=1.0,
                logger=logger,
            )
        assert "took >1.0 seconds to respond" in logs[0]["message"]

        with pytest.raises(RuntimeError):
            await post_safely(
                "http://test/noncompliant",
                {},
                client=client,
                logger=logger,
            )
        assert "non-TRAPI compliant response" in logs[1]["message"]

        with pytest.raises(RuntimeError):
            await post_safely(
                "http://test/doesnotexist",
                {},
                client=client,
                logger=logger,
            )
        assert "Error response" in logs[2]["message"]

        with pytest.raises(RuntimeError):
            await post_safely(
                "http://doesnotexist",
                {},
                logger=logger,
            )
        assert "Error contacting" in logs[3]["message"]

        with pytest.raises(RuntimeError):
            await post_safely(
                "http://test/nonjson",
                {},
                client=client,
                logger=logger,
            )
        assert "bad JSON data" in logs[4]["message"]
