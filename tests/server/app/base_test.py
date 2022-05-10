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

import urllib3
import multiprocessing
import pkgutil

import yaml

import socket
from contextlib import closing


# taken from https://stackoverflow.com/a/45690594
def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('localhost', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


class BaseTest(unittest.TestCase):
    servers = None
    flask = None
    tornado = None

    @classmethod
    def setUpClass(cls) -> None:
        data = pkgutil.get_data('tests', 'test_config.yml')
        config = yaml.safe_load(data)
        flask_port = find_free_port()
        cls.servers = {'flask': f'http://127.0.0.1:{flask_port}'}
        cls.flask = multiprocessing.Process(
            target=flask_server.serve,
            args=(config, '127.0.0.1', flask_port, False, False)
        )
        cls.flask.start()

        tornado_port = find_free_port()
        cls.servers['tornado'] = f'http://127.0.0.1:{tornado_port}'
        cls.tornado = multiprocessing.Process(
            target=tornado_server.serve,
            args=(config, '127.0.0.1', tornado_port, False, False)
        )
        cls.tornado.start()

        cls.http = urllib3.PoolManager()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.flask.terminate()
        cls.tornado.terminate()
