#!/usr/bin/env python3
'''
Class for querying the SmartAPI registry for TRAPI 1.1 endpoints
There is no caching. All gets trigger a fresh query
'''

#### FIXME replace this with httpx
import requests

class SmartAPI:


    def __init__(self):
        self.base_url = 'http://smart-api.info/api'


    def get_operations_endpoints(self):
        '''
        Returns a list of all endpoints that support at least one workflow operation
        '''

        endpoints = self.get_trapi_endpoints()
        if endpoints is None:
            return

        operations_endpoints = []
        for endpoint in endpoints:
            if endpoint['operations'] is not None:
                operations_endpoints.append(endpoint)

        if len(operations_endpoints) == 0:
            return None

        return operations_endpoints


    def get_trapi_endpoints(self):
        '''
        Returns a list of all endpoints that match a query for TRAPI
        '''

        response_content = requests.get( self.base_url + '/query?limit=1000&q=TRAPI', headers={'accept': 'application/json'})

        if response_content.status_code != 200:
            return

        #### Unpack the response content into a dict
        try:
            response_dict = response_content.json()
        except:
            return

        endpoints = []

        if 'hits' in response_dict:
            for hit in response_dict['hits']:
                endpoint_info = { 'url': None, 'operations': None, 'version': None }
                if 'servers' in hit:
                    for server in hit['servers']:
                        endpoint_info['url'] = server['url']
                if 'info' in hit:
                    if 'x-trapi' in hit['info']:
                        if 'version' in hit['info']['x-trapi']:
                            endpoint_info['version'] = hit['info']['x-trapi']['version']
                        if 'operations' in hit['info']['x-trapi']:
                            endpoint_info['operations'] = hit['info']['x-trapi']['operations']
                    endpoints.append(endpoint_info)

        if len(endpoints) == 0:
            return None

        return endpoints



def main():

    import json
    import argparse

    argparser = argparse.ArgumentParser(description='CLI testing of the ResponseCache class')
    argparser.add_argument('--get_trapi_endpoints', action='count', help='Get a list of TRAPI 1.1 endpoints')
    argparser.add_argument('--get_operations_endpoints', action='count', help='Get a list of TRAPI 1.1 endpoints that support operations')
    args = argparser.parse_args()

    if args.get_trapi_endpoints is None and args.get_operations_endpoints is None:
        argparser.print_help()
        exit()

    smartapi = SmartAPI()

    if args.get_trapi_endpoints:
        endpoints = smartapi.get_trapi_endpoints()
        print(json.dumps(endpoints,sort_keys=True,indent=2))

    if args.get_operations_endpoints:
        endpoints = smartapi.get_operations_endpoints()
        print(json.dumps(endpoints,sort_keys=True,indent=2))


if __name__ == "__main__":
    main()

