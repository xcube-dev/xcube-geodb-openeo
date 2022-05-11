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
            self.assertEqual(2, len(items_data['features']), msg)

            self._assert_hamburg(items_data['features'][0], msg)
            self._assert_paderborn(items_data['features'][1], msg)

    def test_get_item(self):
        for server_name in self.servers:
            base_url = self.servers[server_name]
            url = f'{base_url}' \
                  f'{api.API_URL_PREFIX}/collections/collection_1/items/1'
            msg = f'in server {server_name} running on {url}'
            response = self.http.request('GET', url)
            self.assertEqual(200, response.status, msg)
            item_data = json.loads(response.data)
            self._assert_paderborn(item_data, msg)

    def test_get_items_filtered(self):
        for server_name in self.servers:
            base_url = self.servers[server_name]
            url = f'{base_url}' \
                  f'{api.API_URL_PREFIX}/collections/collection_1/items' \
                  f'?limit=1&offset=1'
            msg = f'in server {server_name} running on {url}'
            response = self.http.request('GET', url)
            self.assertEqual(200, response.status, msg)
            items_data = json.loads(response.data)
            self.assertIsNotNone(items_data, msg)
            self.assertEqual('FeatureCollection', items_data['type'], msg)
            self.assertIsNotNone(items_data['features'], msg)
            self.assertEqual(1, len(items_data['features']), msg)
            self._assert_paderborn(items_data['features'][0], msg)

    def test_get_items_invalid_filter(self):
        for server_name in self.servers:
            base_url = self.servers[server_name]
            for invalid_limit in [-1, 0, 10001]:
                url = f'{base_url}' \
                      f'{api.API_URL_PREFIX}/collections/collection_1/items' \
                      f'?limit={invalid_limit}'
                msg = f'in server {server_name} running on {url}'
                response = self.http.request('GET', url)
                self.assertEqual(500, response.status, msg)

    def _assert_paderborn(self, item_data, msg):
        self.assertIsNotNone(item_data, msg)
        self.assertEqual('2.3.4', item_data['stac_version'])
        self.assertEqual(['xcube-geodb'], item_data['stac_extensions'])
        self.assertEqual('Feature', item_data['type'])
        self.assertEqual('1', item_data['id'], msg)
        self.assertEqual(['8.7000', '51.3000', '8.8000', '51.8000'],
                         item_data['bbox'], msg)
        self.assertEqual({'type': 'Polygon', 'coordinates': [[[8.7, 51.3],
                                                              [8.7, 51.8],
                                                              [8.8, 51.8],
                                                              [8.8, 51.3],
                                                              [8.7, 51.3]
                                                              ]]},
                         item_data['geometry'], msg)
        self.assertEqual({'name': 'paderborn', 'population': 150000},
                         item_data['properties'], msg)

    def _assert_hamburg(self, item_data, msg):
        self.assertEqual('2.3.4', item_data['stac_version'], msg)
        self.assertEqual(['xcube-geodb'], item_data['stac_extensions'], msg)
        self.assertEqual('Feature', item_data['type'], msg)
        self.assertEqual('0', item_data['id'], msg)
        self.assertEqual(['9.0000', '52.0000', '11.0000', '54.0000'],
                         item_data['bbox'], msg)
        self.assertEqual({'type': 'Polygon', 'coordinates': [[[9, 52],
                                                              [9, 54],
                                                              [11, 54],
                                                              [11, 52],
                                                              [10, 53],
                                                              [9.8, 53.4],
                                                              [9.2, 52.1],
                                                              [9, 52]]]},
                         item_data['geometry'], msg)
        self.assertEqual({'name': 'hamburg', 'population': 1700000},
                         item_data['properties'], msg)