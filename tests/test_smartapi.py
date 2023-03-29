import logging

from app.smartapi import SmartAPI

logger = logging.getLogger()


def test_production_get_trapi_endpoints():
    logger.info("test that maturity matches 'production' filter")
    smartapi = SmartAPI(maturity="production")
    trapi_endpoints = smartapi.get_trapi_endpoints()
    assert trapi_endpoints is not None and len(trapi_endpoints) > 0
    for entry in trapi_endpoints:
        assert entry["x-maturity"] == "production"


def test_development_get_trapi_endpoints():
    logger.info("test that maturity matches 'development' filter")
    smartapi = SmartAPI(maturity="development")
    trapi_endpoints = smartapi.get_trapi_endpoints()
    assert trapi_endpoints is not None and len(trapi_endpoints) > 0
    for entry in trapi_endpoints:
        assert entry["x-maturity"] == "development"


def test_get_operations_endpoints():
    logger.info("test get_operations_endpoints")
    smartapi = SmartAPI(maturity="production")
    operations_endpoints = smartapi.get_operations_endpoints()
    assert operations_endpoints is not None and len(operations_endpoints) > 0
    for entry in operations_endpoints:
        assert entry["operations"] is not None
