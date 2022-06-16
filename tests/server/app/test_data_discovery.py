import json
import pkgutil
from typing import Dict

import yaml
from xcube.constants import EXTENSION_POINT_SERVER_APIS
from xcube.server.testing import ServerTest
from xcube.util import extension
from xcube.util.extension import ExtensionRegistry


class DataDiscoveryTest(ServerTest):

    def add_extension(self, er: ExtensionRegistry) -> None:
        er.add_extension(loader=extension.import_component('xcube_geodb_openeo.api:api'),
                         point=EXTENSION_POINT_SERVER_APIS, name='geodb-openeo')

    def add_config(self, config: Dict):
        data = pkgutil.get_data('tests', 'test_config.yml')
        config.update(yaml.safe_load(data))

    def test_collections(self):
        url = f'http://localhost:{self.port}/collections'
        response = self.http.request('GET', url)
        self.assertEqual(200, response.status)
        collections_data = json.loads(response.data)
        self.assertIsNotNone(collections_data['collections'])
        self.assertIsNotNone(collections_data['links'])

    def test_collection(self):
        url = f'http://localhost:{self.port}/collections/collection_1'
        response = self.http.request('GET', url)
        self.assertEqual(200, response.status)
        collection_data = json.loads(response.data)
        self.assertIsNotNone(collection_data)

    def test_get_items(self):
        url = f'http://localhost:{self.port}/collections/collection_1/items'
        response = self.http.request('GET', url)
        self.assertEqual(200, response.status)
        items_data = json.loads(response.data)
        self.assertIsNotNone(items_data)
        self.assertEqual('FeatureCollection', items_data['type'])
        self.assertIsNotNone(items_data['features'])
        self.assertEqual(2, len(items_data['features']))

        self._assert_hamburg(items_data['features'][0])
        self._assert_paderborn(items_data['features'][1])

    def test_get_item(self):
        url = f'http://localhost:{self.port}/collections/collection_1/items/1'
        response = self.http.request('GET', url)
        self.assertEqual(200, response.status)
        item_data = json.loads(response.data)
        self._assert_paderborn(item_data)

    def test_get_items_filtered(self):
        url = f'http://localhost:{self.port}/collections/collection_1/items' \
              f'?limit=1&offset=1'
        response = self.http.request('GET', url)
        self.assertEqual(200, response.status)
        items_data = json.loads(response.data)
        self.assertIsNotNone(items_data)
        self.assertEqual('FeatureCollection', items_data['type'])
        self.assertIsNotNone(items_data['features'])
        self.assertEqual(1, len(items_data['features']))
        self._assert_paderborn(items_data['features'][0])

    def test_get_items_invalid_filter(self):
        for invalid_limit in [-1, 0, 10001]:
            url = f'http://localhost:{self.port}/' \
                  f'collections/collection_1/items' \
                  f'?limit={invalid_limit}'
            response = self.http.request('GET', url)
            self.assertEqual(500, response.status)

    def test_get_items_by_bbox(self):
        bbox_param = '?bbox=9.01,50.01,10.01,51.01'
        url = f'http://localhost:{self.port}' \
              f'/collections/collection_1/items' \
              f'{bbox_param}'
        response = self.http.request('GET', url)
        self.assertEqual(200, response.status)
        items_data = json.loads(response.data)
        self.assertEqual('FeatureCollection', items_data['type'])
        self.assertIsNotNone(items_data['features'])
        self.assertEqual(1, len(items_data['features']))

    def _assert_paderborn(self, item_data):
        self.assertIsNotNone(item_data)
        self.assertEqual('0.9.0', item_data['stac_version'])
        self.assertEqual(['xcube-geodb'], item_data['stac_extensions'])
        self.assertEqual('Feature', item_data['type'])
        self.assertEqual('1', item_data['id'])
        self.assertEqual(['8.7000', '51.3000', '8.8000', '51.8000'],
                         item_data['bbox'])
        self.assertEqual({'type': 'Polygon', 'coordinates': [[[8.7, 51.3],
                                                              [8.7, 51.8],
                                                              [8.8, 51.8],
                                                              [8.8, 51.3],
                                                              [8.7, 51.3]
                                                              ]]},
                         item_data['geometry'])
        self.assertEqual({'name': 'paderborn', 'population': 150000},
                         item_data['properties'])

    def _assert_hamburg(self, item_data):
        self.assertEqual('0.9.0', item_data['stac_version'])
        self.assertEqual(['xcube-geodb'], item_data['stac_extensions'])
        self.assertEqual('Feature', item_data['type'])
        self.assertEqual('0', item_data['id'])
        self.assertEqual(['9.0000', '52.0000', '11.0000', '54.0000'],
                         item_data['bbox'])
        self.assertEqual({'type': 'Polygon', 'coordinates': [[[9, 52],
                                                              [9, 54],
                                                              [11, 54],
                                                              [11, 52],
                                                              [10, 53],
                                                              [9.8, 53.4],
                                                              [9.2, 52.1],
                                                              [9, 52]]]},
                         item_data['geometry'])
        self.assertEqual({'name': 'hamburg', 'population': 1700000},
                         item_data['properties'])
