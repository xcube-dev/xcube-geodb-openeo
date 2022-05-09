import xcube_geodb_openeo.server.api as api
import json

from .base_test import BaseTest


class DataDiscoveryTest(BaseTest):
    flask = None
    tornado = None

    def test_collections(self):
        for server_name in self.servers:
            base_url = self.servers[server_name]
            url = f'{base_url}{api.API_URL_PREFIX}/collections'
            msg = f'in server {server_name} running on {url}'
            response = self.http.request('GET', url)
            self.assertEqual(200, response.status, msg)
            collections_data = json.loads(response.data)
            self.assertIsNotNone(collections_data['collections'], msg)
            self.assertIsNotNone(collections_data['links'], msg)

    def test_collection(self):
        for server_name in self.servers:
            base_url = self.servers[server_name]
            url = f'{base_url}{api.API_URL_PREFIX}/collections/collection_1'
            msg = f'in server {server_name} running on {url}'
            response = self.http.request('GET', url)
            self.assertEqual(200, response.status, msg)
            collection_data = json.loads(response.data)
            self.assertIsNotNone(collection_data, msg)

    def test_get_items(self):
        for server_name in self.servers:
            base_url = self.servers[server_name]
            url = f'{base_url}' \
                  f'{api.API_URL_PREFIX}/collections/collection_1/items'
            msg = f'in server {server_name} running on {url}'
            response = self.http.request('GET', url)
            self.assertEqual(200, response.status, msg)
            items_data = json.loads(response.data)
            self.assertIsNotNone(items_data, msg)
            self.assertEqual('FeatureCollection', items_data['type'], msg)
            self.assertIsNotNone(items_data['features'], msg)
