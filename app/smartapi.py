"""SmartAPI registry access utility."""
from functools import cache

import os
import httpx


class SmartAPI:
    """SmartAPI."""

    def __init__(self, maturity):
        """Initialize."""
        self.base_url = "http://smart-api.info/api"
        # get workflow-runner maturity level
        self.maturity = maturity

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
                if "/query" not in hit["paths"].keys():
                    continue
            except KeyError:
                continue
            try:
                url = None
                x_maturity = None
                # check the maturity level against workflow-runner maturity
                for server in hit["servers"]:
                    if server["x-maturity"] == self.maturity:
                        x_maturity = server["x-maturity"]
                        url = server.get("url", None)
                        break
                if x_maturity is None:
                    continue
            except (KeyError):
                continue
            try:
                source_url = hit["_meta"]["url"]
            except (KeyError, IndexError):
                source_url = None
            try:
                version = hit["info"]["x-trapi"]["version"]
            except KeyError:
                version = None
            try:
                operations = hit["info"]["x-trapi"]["operations"]
            except KeyError:
                operations = None
            try:
                title = hit["info"]["title"]
            except KeyError:
                title = None
            try:
                infores = hit["info"]["x-translator"]["infores"]
            except KeyError:
                infores = None
            endpoints.append({
                "title": title,
                "source_url": source_url,
                "url": url,
                "operations": operations,
                "version": version,
                "x-maturity": x_maturity,
                "infores": infores
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
