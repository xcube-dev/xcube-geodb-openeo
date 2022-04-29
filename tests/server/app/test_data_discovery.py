import unittest

import xcube_geodb_openeo.server.app.flask as flask_server
import xcube_geodb_openeo.server.app.tornado as tornado_server
import xcube_geodb_openeo.server.cli as cli
import xcube_geodb_openeo.server.api as api
import urllib3
import multiprocessing
import json

from xcube_geodb_openeo.server.config import load_config


class DataDiscoveryTest(unittest.TestCase):
    flask = None
    tornado = None

    @classmethod
    def setUpClass(cls) -> None:
        config = load_config('../../test_config.yml')

        cls.flask_base_url = f'http://127.0.0.1:{cli.DEFAULT_PORT + 1}'

        cls.flask = multiprocessing.Process(
            target=flask_server.serve,
            args=(config, '127.0.0.1', cli.DEFAULT_PORT + 1,
                  False, False)
        )
        cls.flask.start()

        cls.tornado_base_url = f'http://127.0.0.1:{cli.DEFAULT_PORT + 2}'
        cls.tornado = multiprocessing.Process(
            target=tornado_server.serve,
            args=(config, '127.0.0.1', cli.DEFAULT_PORT + 2,
                  False, False)
        )
        cls.tornado.start()

        cls.http = urllib3.PoolManager()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.flask.terminate()
        cls.tornado.terminate()

    def test_collections(self):
        for base_url in [self.flask_base_url, self.tornado_base_url]:
            url = f'{base_url}{api.API_URL_PREFIX}/collections'
            response = self.http.request('GET', url)
            self.assertEqual(200, response.status, base_url)
            collections_data = json.loads(response.data)
            self.assertIsNotNone(collections_data['collections'])
            self.assertIsNotNone(collections_data['links'])

    def test_collection(self):
        for base_url in [self.flask_base_url, self.tornado_base_url]:
            url = f'{base_url}{api.API_URL_PREFIX}/collections/collection_1'
            response = self.http.request('GET', url)
            self.assertEqual(200, response.status, base_url)
            collection_data = json.loads(response.data)
            self.assertIsNotNone(collection_data)

    def test_get_items(self):
        for base_url in [self.flask_base_url, self.tornado_base_url]:
            url = f'{base_url}' \
                  f'{api.API_URL_PREFIX}/collections/collection_1/items'
            response = self.http.request('GET', url)
            self.assertEqual(200, response.status, base_url)
            items_data = json.loads(response.data)
            self.assertIsNotNone(items_data)
            self.assertEqual('FeatureCollection', items_data['type'])
            self.assertIsNotNone('', items_data['features'])
            self.assertEqual(2, len(items_data['features']))
            self.assertEqual(['9.0000', '52.0000', '11.0000', '54.0000'],
                             items_data['features'][0]['bbox'])
            self.assertEqual(['8.7000', '51.3000', '8.8000', '51.8000'],
                             items_data['features'][1]['bbox'])

            self.assertEqual('0.1.0',
                             items_data['features'][0]['stac_version'])
            self.assertEqual(['xcube-geodb'],
                             items_data['features'][0]['stac_extensions'])
            self.assertEqual('Feature',
                             items_data['features'][0]['type'])

            self.assertEqual('0.1.0',
                             items_data['features'][1]['stac_version'])
            self.assertEqual(['xcube-geodb'],
                             items_data['features'][1]['stac_extensions'])
            self.assertEqual('Feature',
                             items_data['features'][1]['type'])
