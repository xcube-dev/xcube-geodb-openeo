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
            self.assertIsNotNone(items_data)
            self.assertEqual('FeatureCollection', items_data['type'], msg)
            self.assertIsNotNone(items_data['features'], msg)
            self.assertEqual(2, len(items_data['features']), msg)

            self.assertEqual('2.3.4',
                             items_data['features'][0]['stac_version'], msg)
            self.assertEqual(['xcube-geodb'],
                             items_data['features'][0]['stac_extensions'], msg)
            self.assertEqual('Feature',
                             items_data['features'][0]['type'], msg)
            self.assertEqual('0',
                             items_data['features'][0]['id'], msg)
            self.assertEqual(['9.0000', '52.0000', '11.0000', '54.0000'],
                             items_data['features'][0]['bbox'], msg)
            self.assertEqual({'type': 'Polygon', 'coordinates': [[[9, 52],
                                                                  [9, 54],
                                                                  [11, 54],
                                                                  [11, 52],
                                                                  [10, 53],
                                                                  [9.8, 53.4],
                                                                  [9.2, 52.1],
                                                                  [9, 52]]]},
                             items_data['features'][0]['geometry'], msg)
            self.assertEqual({'name': 'hamburg', 'population': 1700000},
                             items_data['features'][0]['properties'], msg)

            self.assertEqual('2.3.4',
                             items_data['features'][1]['stac_version'])
            self.assertEqual(['xcube-geodb'],
                             items_data['features'][1]['stac_extensions'])
            self.assertEqual('Feature',
                             items_data['features'][1]['type'])
            self.assertEqual('1',
                             items_data['features'][1]['id'], msg)
            self.assertEqual(['8.7000', '51.3000', '8.8000', '51.8000'],
                             items_data['features'][1]['bbox'], msg)
            self.assertEqual({'type': 'Polygon', 'coordinates': [[[8.7, 51.3],
                                                                  [8.7, 51.8],
                                                                  [8.8, 51.8],
                                                                  [8.8, 51.3],
                                                                  [8.7, 51.3]
                                                                  ]]},
                             items_data['features'][1]['geometry'], msg)
            self.assertEqual({'name': 'paderborn', 'population': 150000},
                             items_data['features'][1]['properties'], msg)
