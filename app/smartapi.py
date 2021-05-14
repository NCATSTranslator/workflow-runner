"""SmartAPI registry access utility."""
from functools import cache

import httpx


class SmartAPI:
    """SmartAPI."""

    def __init__(self):
        """Initialize."""
        self.base_url = "http://smart-api.info/api"

    @cache
    def get_operations_endpoints(self):
        """Find all endpoints that support at least one workflow operation."""
        endpoints = self.get_trapi_endpoints()

        operations_endpoints = []
        for endpoint in endpoints:
            if endpoint["operations"] is not None:
                operations_endpoints.append(endpoint)

        return operations_endpoints

    @cache
    def get_trapi_endpoints(self):
        """Find all endpoints that match a query for TRAPI."""
        response_content = httpx.get(
            self.base_url + "/query?limit=1000&q=TRAPI",
            headers={"accept": "application/json"},
        )

        response_content.raise_for_status()
        response_dict = response_content.json()

        endpoints = []
        for hit in response_dict["hits"]:
            try:
                url = hit["servers"][0]["url"]
            except (KeyError, IndexError):
                url = None
            try:
                version = hit["info"]["x-trapi"]["version"]
            except KeyError:
                version = None
            try:
                operations = hit["info"]["x-trapi"]["operations"]
            except KeyError:
                operations = None
            endpoints.append({
                "url": url,
                "operations": operations,
                "version": version,
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
