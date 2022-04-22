import unittest

import xcube_geodb_openeo.server.app.flask as flask_server
import xcube_geodb_openeo.server.app.tornado as tornado_server
import xcube_geodb_openeo.server.cli as cli
import xcube_geodb_openeo.server.api as api
import urllib3
import multiprocessing
import json


class BackendInfoTest(unittest.TestCase):
    flask = None
    tornado = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.flask_base_url = f'http://127.0.0.1:{cli.DEFAULT_PORT + 1}'
        cls.flask = multiprocessing.Process(
            target=flask_server.serve,
            args=({
                      'api_version': '0.1.2',
                      'stac_version': '2.3.4',
                      'url': 'http://xcube-geoDB-openEO.de'
                  }, '127.0.0.1', cli.DEFAULT_PORT + 1, False, False)
        )
        cls.flask.start()

        cls.tornado_base_url = f'http://127.0.0.1:{cli.DEFAULT_PORT + 2}'
        cls.tornado = multiprocessing.Process(
            target=tornado_server.serve,
            args=({
                      'api_version': '0.1.2',
                      'stac_version': '2.3.4',
                      'url': 'http://xcube-geoDB-openEO.de'
                  }, '127.0.0.1', cli.DEFAULT_PORT + 2, False, False)
        )
        cls.tornado.start()

        cls.http = urllib3.PoolManager()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.flask.terminate()
        cls.tornado.terminate()

    def test_root_endpoint(self):
        response = self.http.request('GET', f'{self.flask_base_url}'
                                            f'{api.API_URL_PREFIX}/')
        self.do_test_root_endpoint(response)
        response = self.http.request('GET', f'{self.tornado_base_url}'
                                            f'{api.API_URL_PREFIX}/')
        self.do_test_root_endpoint(response)

    def do_test_root_endpoint(self, response):
        self.assertEqual(200, response.status)
        self.assertTrue('application/json' in response.headers['content-type'])
        metainfo = json.loads(response.data)
        self.assertEqual('0.1.2', metainfo['api_version'])
        self.assertEqual('0.0.1.dev0', metainfo['backend_version'])
        self.assertEqual('2.3.4', metainfo['stac_version'])
        self.assertEqual('catalog', metainfo['type'])
        self.assertEqual('xcube-geodb-openeo', metainfo['id'])
        self.assertEqual('xcube geoDB for openEO', metainfo['title'])
        self.assertEqual('tbd', metainfo['description'])
        self.assertEqual('/collections', metainfo['endpoints'][0]['path'])
        self.assertEqual('GET', metainfo['endpoints'][0]['methods'][0])
        self.assertIsNotNone(metainfo['links'])

    def test_well_known_info(self):
        response = self.http.request(
            'GET', f'{self.flask_base_url}/.well-known/openeo'
        )
        self.do_test_well_known_info(response)
        response = self.http.request(
            'GET', f'{self.tornado_base_url}/.well-known/openeo'
        )
        self.do_test_well_known_info(response)

    def do_test_well_known_info(self, response):
        self.assertEqual(200, response.status)
        well_known_data = json.loads(response.data)
        self.assertEqual('http://xcube-geoDB-openEO.de',
                         well_known_data['versions'][0]['url'])
        self.assertEqual('0.1.2',
                         well_known_data['versions'][0]['api_version'])
