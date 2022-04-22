import unittest

import xcube_geodb_openeo.server.app.flask as flask_server
import xcube_geodb_openeo.server.app.tornado as tornado_server
import xcube_geodb_openeo.server.cli as cli
import xcube_geodb_openeo.server.api as api
import urllib3
import multiprocessing
import json


class CapabilitiesTest(unittest.TestCase):
    flask = None
    tornado = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.flask_base_url = f'http://127.0.0.1:{cli.DEFAULT_PORT + 1}'
        test_conf = {
            'api_version': '0.1.2',
            'stac_version': '2.3.4',
            'url': 'http://xcube-geoDB-openEO.de',
            'id': 'xcube-geodb-openeo',
            'title': 'xcube geoDB Server, openEO API',
            'description': 'Catalog of geoDB collections.'
        }
        cls.flask = multiprocessing.Process(
            target=flask_server.serve,
            args=(test_conf, '127.0.0.1', cli.DEFAULT_PORT + 1, False, False)
        )
        cls.flask.start()

        cls.tornado_base_url = f'http://127.0.0.1:{cli.DEFAULT_PORT + 2}'
        cls.tornado = multiprocessing.Process(
            target=tornado_server.serve,
            args=(test_conf, '127.0.0.1', cli.DEFAULT_PORT + 2, False, False)
        )
        cls.tornado.start()

        cls.http = urllib3.PoolManager()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.flask.terminate()
        cls.tornado.terminate()

    def test_root(self):
        for url in [self.flask_base_url, self.tornado_base_url]:
            response = self.http.request('GET', f'{url}'
                                                f'{api.API_URL_PREFIX}/')
            self.assertEqual(200, response.status, url)
            self.assertTrue(
                'application/json' in response.headers['content-type'], url
            )
            metainfo = json.loads(response.data)
            self.assertEqual('0.1.2', metainfo['api_version'], url)
            self.assertEqual('0.0.1.dev0', metainfo['backend_version'], url)
            self.assertEqual('2.3.4', metainfo['stac_version'], url)
            self.assertEqual('catalog', metainfo['type'], url)
            self.assertEqual('xcube-geodb-openeo', metainfo['id'], url)
            self.assertEqual(
                'xcube geoDB Server, openEO API', metainfo['title'], url
            )
            self.assertEqual(
                'Catalog of geoDB collections.', metainfo['description'], url)
            self.assertEqual(
                '/collections', metainfo['endpoints'][0]['path'], url)
            self.assertEqual(
                'GET', metainfo['endpoints'][0]['methods'][0], url)
            self.assertIsNotNone(metainfo['links'])

    def test_well_known_info(self):
        for url in [self.flask_base_url, self.tornado_base_url]:
            response = self.http.request(
                'GET', f'{url}/.well-known/openeo'
            )
            self.assertEqual(200, response.status, url)
            well_known_data = json.loads(response.data)
            self.assertEqual('http://xcube-geoDB-openEO.de',
                             well_known_data['versions'][0]['url'], url)
            self.assertEqual('0.1.2',
                             well_known_data['versions'][0]['api_version'],
                             url)

    def test_conformance(self):
        for url in [self.flask_base_url, self.tornado_base_url]:
            response = self.http.request(
                'GET', f'{url}{api.API_URL_PREFIX}/conformance'
            )
            self.assertEqual(200, response.status, url)
            conformance_data = json.loads(response.data)
            self.assertIsNotNone(conformance_data['conformsTo'], url)
