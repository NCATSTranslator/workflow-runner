"""SmartAPI registry access utility."""
from functools import cache
from typing import Optional, Callable
import httpx


class SmartAPI:
    """SmartAPI."""

    def __init__(self, maturity, trapi):
        """Initialize."""
        self.base_url = "http://smart-api.info/api"
        # get workflow-runner maturity level
        self.maturity = maturity
        self.trapi = trapi

    @cache
    def get_operations_endpoints(
        self,
        endpoint_filter_function: Optional[Callable] = None,
        server_filter_function: Optional[Callable] = None,
    ):
        """Find all endpoints that support at least one workflow operation."""
        endpoints = self.get_trapi_endpoints(
            endpoint_filter_function, server_filter_function
        )

        operations_endpoints = []
        for endpoint in endpoints:
            if endpoint["operations"] is not None:
                operations_endpoints.append(endpoint)

        return operations_endpoints

    @cache
    def get_trapi_endpoints(
        self,
        endpoint_filter_function: Optional[Callable] = None,
        server_filter_function: Optional[Callable] = None,
    ):
        """Find all endpoints that match a query for TRAPI."""
        response_content = httpx.get(
            self.base_url + "/query?limit=1000&q=TRAPI",
            headers={"accept": "application/json"},
        )

        response_content.raise_for_status()
        response_dict = response_content.json()

        hits = response_dict["hits"]
        if endpoint_filter_function is not None:
            hits = filter(endpoint_filter_function, hits)

        endpoints = []
        for hit in hits:
            try:
                if "/query" not in hit["paths"].keys():
                    continue
            except KeyError:
                continue
            try:
                url = None
                x_maturity = None
                # check the maturity level against workflow-runner maturity
                servers = hit["servers"]
                if server_filter_function is not None:
                    servers = filter(server_filter_function, servers)
                for server in servers:
                    if server["x-maturity"] == self.maturity:
                        x_maturity = server["x-maturity"]
                        url = server.get("url", None)
                        break
                if x_maturity is None:
                    continue
            except KeyError:
                continue
            try:
                source_url = hit["_meta"]["url"]
            except (KeyError, IndexError):
                source_url = None
            try:
                version = None
                regex = re.compile("[0-9].[0-9].")
                trapi_minor = regex.match(self.trapi).group()
                # check the TRAPI version against workflow-runner TRAPI version
                if hit["info"]["x-trapi"]["version"].startswith(trapi_minor):
                    version = hit["info"]["x-trapi"]["version"]
                else:
                    continue
            except KeyError:
                continue
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
            endpoints.append(
                {
                    "title": title,
                    "source_url": source_url,
                    "url": url,
                    "operations": operations,
                    "version": version,
                    "x-maturity": x_maturity,
                    "infores": infores,
                }
            )

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
    argparser.add_argument(
        "-m",
        "--maturity",
        type=str,
        choices=["development", "production", "ci", "test"],
        nargs=1,
        help="development, production, ci, test",
    )

    args = argparser.parse_args()

    if args.maturity is None:
        argparser.print_help()
        return

    if args.get_trapi_endpoints is None and args.get_operations_endpoints is None:
        argparser.print_help()
        return

    smartapi = SmartAPI(maturity=args.maturity[0])

    if args.get_trapi_endpoints:

        # this will remove the entire "hit", even if/when there are multiple "servers"
        # def remove_bad_endpoints(hit):
        #     for server in hit["servers"]:
        #         url = server.get("url", None)
        #         if url == "https://arax.ncats.io/beta/api/arax/v1.3":
        #             return True
        #     return False

        def skip_arax_beta(server):
            url = server.get("url", None)
            if url == "https://arax.ncats.io/beta/api/arax/v1.3":
                return False
            else:
                return True

        endpoints = smartapi.get_trapi_endpoints(None, skip_arax_beta)
        print(json.dumps(endpoints, sort_keys=True, indent=2))
        for endpoint in endpoints:
            print(endpoint["title"])

    if args.get_operations_endpoints:
        endpoints = smartapi.get_operations_endpoints()
        print(json.dumps(endpoints, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
