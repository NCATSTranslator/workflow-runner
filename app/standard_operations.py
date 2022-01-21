"""Translator Standards Operations registry access utility."""
from functools import cache

import httpx

class StandardOperations:
    """StandardOperations."""

    def __init__(self):
        """Initialize."""
        self.base_url = "https://standards.ncats.io/operation/1.2.0/schema"

    @cache
    def get_operations(self):
        """Find all endpoints that match a query for TRAPI."""
        response_content = httpx.get(
            self.base_url,
            headers={"accept": "application/json"},
        )

        response_content.raise_for_status()
        response_dict = response_content.json()

        operations = {}
        for op, props in response_dict["$defs"].items():
            
            operations[op] = {
                "id": op,
                "description": props.get('description',''),
                "properties": props.get('properties',{}),
                "additionalProperties": props.get('additionalProperties',False),
                "unique": props.get('unique', False)
            }

        return operations