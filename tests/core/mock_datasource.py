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
from typing import Any
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Tuple

import geopandas
from pandas import DataFrame
from shapely.geometry import Polygon

from xcube_geodb_openeo.core.datasource import VectorSource
from xcube_geodb_openeo.core.geodb_datasource import GeoDBVectorSource
from xcube_geodb_openeo.core.vectorcube import VectorCube
import importlib.resources as resources


class MockVectorSource(VectorSource):

    # noinspection PyUnusedLocal
    def __init__(self, config: Mapping[str, Any]):
        with resources.open_text('tests', 'mock_collections.json') as text:
            mock_collections = json.load(text)['_MOCK_COLLECTIONS_LIST']
        self._MOCK_COLLECTIONS = {v["id"]: v for v in mock_collections}

    def get_collection_keys(self) -> Sequence:
        return list(self._MOCK_COLLECTIONS.keys())

    def get_vector_cube(self, collection_id: str, with_items: bool,
                        bbox: Tuple[float, float, float, float] = None,
                        limit: Optional[int] = None, offset: Optional[int] =
                        0) -> Optional[VectorCube]:
        if collection_id == 'non-existent-collection':
            return None
        vector_cube = {}
        data = {
            'id': ['0', '1'],
            'name': ['hamburg', 'paderborn'],
            'geometry': [Polygon(((9, 52), (9, 54), (11, 54), (11, 52),
                                  (10, 53), (9.8, 53.4), (9.2, 52.1),
                                  (9, 52))),
                         Polygon(((8.7, 51.3), (8.7, 51.8), (8.8, 51.8),
                                  (8.8, 51.3), (8.7, 51.3)))
                         ],
            'population': [1700000, 150000]
        }
        collection = geopandas.GeoDataFrame(data, crs="EPSG:4326")
        if bbox:
            # simply dropping one entry; we don't need to test this
            # logic here, as it is implemented within the geoDB module
            collection = collection.drop([1, 1])
        if limit:
            collection = collection[offset:offset + limit]
        vector_cube['id'] = collection_id
        vector_cube['features'] = []
        vector_cube['total_feature_count'] = len(collection)
        if with_items and collection_id != 'empty_collection':
            self.add_items_to_vector_cube(collection, vector_cube)
        GeoDBVectorSource.add_metadata(
            (8, 51, 12, 52), collection_id,
            DataFrame(columns=["collection", "column_name", "data_type"]),
            '0.3.1', vector_cube)
        return vector_cube

    # noinspection PyUnusedLocal
    def transform_bbox(self, collection_id: str,
                       bbox: Tuple[float, float, float, float],
                       crs: int) -> Tuple[float, float, float, float]:
        return bbox
