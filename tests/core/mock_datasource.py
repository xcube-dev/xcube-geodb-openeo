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

import json
from typing import Sequence
from xcube_geodb_openeo.core.datasource import DataSource
from xcube_geodb_openeo.core.vectorcube import VectorCube
import importlib.resources as resources


class MockDataSource(DataSource):

    def __init__(self):
        with resources.open_text('tests', 'mock_collections.json') as text:
            mock_collections = json.load(text)['_MOCK_COLLECTIONS_LIST']
        self._MOCK_COLLECTIONS = {v["id"]: v for v in mock_collections}

    def get_collection_keys(self) -> Sequence:
        return list(self._MOCK_COLLECTIONS.keys())

    def get_vector_cube(self, collection_id) -> VectorCube:
        return self._MOCK_COLLECTIONS[collection_id]
