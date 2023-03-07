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
import math
from typing import Dict, Tuple, Optional

import shapely.geometry
import shapely.wkt
from geopandas import GeoDataFrame

from .vectorcube import VectorCube
from ..defaults import STAC_VERSION, STAC_EXTENSIONS


class DataSource(abc.ABC):

    @abc.abstractmethod
    def get_collection_keys(self):
        pass

    @abc.abstractmethod
    def get_vector_cube(self, collection_id: str, with_items: bool,
                        bbox: Tuple[float, float, float, float],
                        limit: Optional[int] = None,
                        offset: Optional[int] = 0) -> Optional[VectorCube]:
        pass

    @staticmethod
    def _get_coords(feature: Dict) -> Dict:
        geometry = feature['geometry']
        feature_wkt = shapely.wkt.loads(geometry.wkt)
        coords = shapely.geometry.mapping(feature_wkt)
        return coords

    @staticmethod
    def add_items_to_vector_cube(
            collection: GeoDataFrame, vector_cube: VectorCube):
        bounds = collection.bounds
        for i, row in enumerate(collection.iterrows()):
            bbox = bounds.iloc[i]
            feature = row[1]
            coords = DataSource._get_coords(feature)
            properties = {}
            for k, key in enumerate(feature.keys()):
                if not key == 'id' and not \
                        collection.dtypes.values[k].name == 'geometry':
                    if isinstance(feature[key], float) \
                            and math.isnan(float(feature[key])):
                        properties[key] = 'NaN'
                    else:
                        properties[key] = feature[key]

            vector_cube['features'].append({
                'stac_version': STAC_VERSION,
                'stac_extensions': STAC_EXTENSIONS,
                'type': 'Feature',
                'id': feature['id'],
                'bbox': [f'{bbox["minx"]:.4f}',
                         f'{bbox["miny"]:.4f}',
                         f'{bbox["maxx"]:.4f}',
                         f'{bbox["maxy"]:.4f}'],
                'geometry': coords,
                'properties': properties
            })