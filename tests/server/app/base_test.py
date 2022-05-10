# The MIT License (MIT)
# Copyright (c) 2021/2022 by the xcube team and contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import unittest

import xcube_geodb_openeo.server.app.flask as flask_server
import xcube_geodb_openeo.server.app.tornado as tornado_server
import xcube_geodb_openeo.server.cli as cli

import urllib3
import multiprocessing
import pkgutil

import yaml


class BaseTest(unittest.TestCase):
    servers = None
    flask = None
    tornado = None

    @classmethod
    def setUpClass(cls) -> None:
        data = pkgutil.get_data('tests', 'test_config.yml')
        config = yaml.safe_load(data)
        cls.servers = {'flask': f'http://127.0.0.1:{cli.DEFAULT_PORT + 1}'}
        cls.flask = multiprocessing.Process(
            target=flask_server.serve,
            args=(config, '127.0.0.1', cli.DEFAULT_PORT + 1, False, False)
        )
        cls.flask.start()

        cls.servers['tornado'] = f'http://127.0.0.1:{cli.DEFAULT_PORT + 2}'
        cls.tornado = multiprocessing.Process(
            target=tornado_server.serve,
            args=(config, '127.0.0.1', cli.DEFAULT_PORT + 2, False, False)
        )
        cls.tornado.start()

        cls.http = urllib3.PoolManager()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.flask.terminate()
        cls.tornado.terminate()
