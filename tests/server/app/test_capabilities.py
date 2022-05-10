import xcube_geodb_openeo.server.api as api
import json

from .base_test import BaseTest


class CapabilitiesTest(BaseTest):

    def test_root(self):
        for server_name in self.servers:
            url = self.servers[server_name]
            msg = f'in server {server_name} running on {url}'
            response = self.http.request('GET', f'{url}'
                                                f'{api.API_URL_PREFIX}/')
            self.assertEqual(200, response.status, msg)
            self.assertTrue(
                'application/json' in response.headers['content-type'], msg
            )
            metainfo = json.loads(response.data)
            self.assertEqual('0.1.2', metainfo['api_version'], msg)
            self.assertEqual('0.0.1.dev0', metainfo['backend_version'], msg)
            self.assertEqual('2.3.4', metainfo['stac_version'], msg)
            self.assertEqual('catalog', metainfo['type'], msg)
            self.assertEqual('xcube-geodb-openeo', metainfo['id'], msg)
            self.assertEqual(
                'xcube geoDB Server, openEO API', metainfo['title'], msg
            )
            self.assertEqual(
                'Catalog of geoDB collections.', metainfo['description'], msg)
            self.assertEqual(
                '/collections', metainfo['endpoints'][0]['path'], msg)
            self.assertEqual(
                'GET', metainfo['endpoints'][0]['methods'][0], msg)
            self.assertIsNotNone(metainfo['links'])

    def test_well_known_info(self):
        for server_name in self.servers:
            url = self.servers[server_name]
            msg = f'in server {server_name} running on {url}'
            response = self.http.request(
                'GET', f'{url}/.well-known/openeo'
            )
            self.assertEqual(200, response.status, msg)
            well_known_data = json.loads(response.data)
            self.assertEqual('http://xcube-geoDB-openEO.de',
                             well_known_data['versions'][0]['url'], msg)
            self.assertEqual('0.1.2',
                             well_known_data['versions'][0]['api_version'],
                             msg)

    def test_conformance(self):
        for server_name in self.servers:
            url = self.servers[server_name]
            msg = f'in server {server_name} running on {url}'

            response = self.http.request(
                'GET', f'{url}{api.API_URL_PREFIX}/conformance'
            )
            self.assertEqual(200, response.status, msg)
            conformance_data = json.loads(response.data)
            self.assertIsNotNone(conformance_data['conformsTo'], msg)
