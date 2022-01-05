"""Translator Standards Operations registry access utility."""
from functools import cache

import httpx

class StandardOperations:
    """StandardOperations."""

    def __init__(self):
        """Initialize."""
        self.base_url = "https://standards.ncats.io/operation/1.0.1/schema"

    @cache
    def get_operations(self):
        """Find all endpoints that match a query for TRAPI."""
        response_content = httpx.get(
            self.base_url,
            headers={"accept": "application/json"},
        )

        response_content.raise_for_status()
        response_dict = response_content.json()

        operations = []
        for op in response_dict["$defs"]:
            operations.append({
                "source_url": source_url,
                "url": url,
                "operations": operations,
                "version": version,
                "title": title,
                "x-maturity": x_maturity
            })

        return endpoints


def main():
    """Run CLI."""
    import argparse
    import json

    argparser = argparse.ArgumentParser(
        description="CLI testing of the ResponseCache class"
    )
    argparser.add_argument(
        "--get_trapi_endpoints",
        action="count",
        help="Get a list of TRAPI endpoints",
    )
    argparser.add_argument(
        "--get_operations_endpoints",
        action="count",
        help="Get a list of TRAPI endpoints that support operations",
    )
    args = argparser.parse_args()

    if (
        args.get_trapi_endpoints is None
        and args.get_operations_endpoints is None
    ):
        argparser.print_help()
        return

    smartapi = SmartAPI()

    if args.get_trapi_endpoints:
        endpoints = smartapi.get_trapi_endpoints()
        print(json.dumps(endpoints, sort_keys=True, indent=2))

    if args.get_operations_endpoints:
        endpoints = smartapi.get_operations_endpoints()
        print(json.dumps(endpoints, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
