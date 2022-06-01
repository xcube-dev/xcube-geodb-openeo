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

import urllib3
import multiprocessing
import pkgutil
import yaml
import time
import os

import socket
from contextlib import closing

import xcube.cli.main as xcube


# taken from https://stackoverflow.com/a/45690594
from xcube.server.impl.framework.tornado import TornadoFramework


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('localhost', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


class BaseTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.port = find_free_port()
        from xcube.server.server import Server
        data = pkgutil.get_data('tests', 'test_config.yml')
        config = yaml.safe_load(data)
        config['port'] = cls.port
        config['address'] = 'localhost'
        server = Server(framework=TornadoFramework(), config=config)
        server.start()
        import threading
        cls.s = threading.Thread(target=server.start)
        cls.s.daemon = True
        cls.s.start()
        # cls.server.start()

        # xcube.main(args=['serve2', '-c', '../test_config.yml'])

        # data = pkgutil.get_data('tests', 'test_config.yml')
        # config = yaml.safe_load(data)

        cls.http = urllib3.PoolManager()
        print(cls.port, flush=True)


    @classmethod
    def tearDownClass(cls) -> None:
        cls.s.stop()
