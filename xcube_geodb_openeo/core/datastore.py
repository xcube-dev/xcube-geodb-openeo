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

import abc
from typing import Union

from .vectorcube import VectorCube
from ..server.config import Config

from geopandas import GeoDataFrame
from pandas import DataFrame

class DataStore(abc.ABC):

    @abc.abstractmethod
    def get_collection_keys(self):
        pass

    @abc.abstractmethod
    def get_vector_cube(self, collection_id) -> VectorCube:
        pass

    @staticmethod
    def add_collection_to_vector_cube(
            collection: Union[GeoDataFrame, DataFrame],
            collection_id: str,
            vector_cube: VectorCube,
            config: Config):
        bounds = collection.bounds
        vector_cube['id'] = collection_id
        # geometries = collection.to_wkt().get('geometry')
        # print(geometries)
        vector_cube['features'] = []
        for i, row in enumerate(collection.iterrows()):
            bbox = bounds.iloc[i]
            vector_cube['features'].append({
                'stac_version': config['stac_version'],
                'stac_extensions': ['xcube-geodb'],
                'type': 'Feature',
                'id': collection_id,
                'bbox': [f'{bbox["minx"]:.4f}',
                         f'{bbox["miny"]:.4f}',
                         f'{bbox["maxx"]:.4f}',
                         f'{bbox["maxy"]:.4f}']
            })

