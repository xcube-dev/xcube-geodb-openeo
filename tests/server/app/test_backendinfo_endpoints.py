import unittest

import xcube_geodb_openeo.server.app.flask as flask_server
import xcube_geodb_openeo.server.cli as cli
import xcube_geodb_openeo.server.api as api
import urllib3
import multiprocessing
import json


class BackendInfoEndpointTest(unittest.TestCase):

    server = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.url = f'http://127.0.0.1:{cli.DEFAULT_PORT + 1}' \
                  f'{api.API_URL_PREFIX}/'
        cls.server = multiprocessing.Process(
            target=flask_server.serve,
            args=({}, '127.0.0.1', cli.DEFAULT_PORT + 1, False, False)
        )
        cls.server.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.terminate()

    def test_root_endpoint(self):
        http = urllib3.PoolManager()
        response = http.request('GET', self.url)
        self.assertEqual(200, response.status)
        self.assertEqual('application/json', response.headers['content-type'])
        metainfo = json.loads(response.data)
        self.assertEqual('1.1.0', metainfo['api_version'])
        self.assertEqual('0.0.1.dev0', metainfo['backend_version'])
        self.assertEqual('1.0.0', metainfo['stac_version'])
        self.assertEqual('catalog', metainfo['type'])
        self.assertEqual('xcube-geodb-openeo', metainfo['id'])
        self.assertEqual('xcube geoDB for openEO', metainfo['title'])
        self.assertEqual('tbd', metainfo['description'])
        self.assertEqual('/collections', metainfo['endpoints'][0]['path'])
        self.assertEqual('GET', metainfo['endpoints'][0]['methods'][0])
        self.assertIsNotNone(metainfo['links'])
