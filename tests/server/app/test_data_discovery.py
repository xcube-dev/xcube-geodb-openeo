import unittest

import xcube_geodb_openeo.server.app.flask as flask_server
import xcube_geodb_openeo.server.app.tornado as tornado_server
import xcube_geodb_openeo.server.cli as cli
import xcube_geodb_openeo.server.api as api
import urllib3
import multiprocessing
import json


class DataDiscoveryTest(unittest.TestCase):
    flask = None
    tornado = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.flask_base_url = f'http://127.0.0.1:{cli.DEFAULT_PORT + 1}'

        cls.flask = multiprocessing.Process(
            target=flask_server.serve,
            args=({'stac_version': '0.9.0'}, '127.0.0.1', cli.DEFAULT_PORT + 1,
                  False, False)
        )
        cls.flask.start()

        cls.tornado_base_url = f'http://127.0.0.1:{cli.DEFAULT_PORT + 2}'
        cls.tornado = multiprocessing.Process(
            target=tornado_server.serve,
            args=({'stac_version': '0.9.0'}, '127.0.0.1', cli.DEFAULT_PORT + 2,
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

