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
from functools import cached_property
from typing import Dict, Tuple, Optional, List, Mapping, Any

import shapely.geometry
import shapely.wkt
from geopandas import GeoDataFrame
from pandas import DataFrame
from xcube.constants import LOG
from xcube_geodb.core.geodb import GeoDBClient

from .geodb_datasource import GeoDBVectorSource
from .tools import create_geodb_client
from .vectorcube import VectorCube
from ..defaults import STAC_VERSION, STAC_EXTENSIONS


class VectorCubeProvider(abc.ABC):

    @abc.abstractmethod
    def get_collection_keys(self) -> List[Tuple[str, str]]:
        pass

    @abc.abstractmethod
    def get_vector_cube(self, collection_id: Tuple[str, str],
                        bbox: Tuple[float, float, float, float])\
            -> Optional[VectorCube]:
        pass

    @staticmethod
    def add_items_to_vector_cube(
            collection: GeoDataFrame, vector_cube: VectorCube):
        bounds = collection.bounds
        for i, row in enumerate(collection.iterrows()):
            bbox = bounds.iloc[i]
            feature = row[1]
            coords = VectorCubeProvider._get_coords(feature)
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


class GeoDBProvider(VectorCubeProvider):

    def __init__(self, config: Mapping[str, Any]):
        self.config = config

    @cached_property
    def geodb(self) -> GeoDBClient:
        assert self.config
        api_config = self.config['geodb_openeo']
        return create_geodb_client(api_config)

    def get_collection_keys(self) -> List[Tuple[str, str]]:
        collections = self.geodb.get_my_collections()
        result = []
        collection_list = collections.get('collection')
        for idx, database in enumerate(collections.get('database')):
            collection_id = collection_list[idx]
            if collection_id:
                result.append((database, collection_id))

        return result

    def get_vector_cube(self, collection_id: Tuple[str, str],
                        bbox: Tuple[float, float, float, float] = None) \
            -> Optional[VectorCube]:
        (db, name) = collection_id
        LOG.debug(f'Building vector cube for collection '
                  f'{db}~{name}...')

        vector_cube = VectorCube(collection_id,
                                 GeoDBVectorSource(self.config, collection_id))
        LOG.debug(f'  counting collection items...')
        count = self.geodb.count_collection_by_bbox(name, bbox, database=db) \
            if bbox \
            else self.geodb.count_collection_rows(name, database=db,
                                                  exact_count=True)
        LOG.debug(f'  ...done.')
        properties = self.geodb.get_properties(name, db)
        metadata = self._create_metadata(properties, f'{name}', count)
        vector_cube._metadata = metadata
        LOG.debug("...done building vector cube.")
        return vector_cube

    @staticmethod
    def _create_metadata(properties: DataFrame, title: str,
                         collection_bbox: Tuple[float, float, float, float],
                         count: int) -> {}:
        summaries = {
            'properties': []
        }
        for p in properties['column_name'].to_list():
            summaries['properties'].append({'name': p})
        metadata = {
            'title': title,
            'extent': {
                'spatial': {
                    'bbox': [collection_bbox],
                    'crs': 'http://www.opengis.net/def/crs/OGC/1.3/CRS84'
                },
                'temporal': {
                    'interval': [[None, None]]
                    # todo - maybe define a list of possible property names to
                    #  scan for the temporal interval, such as start_date,
                    #  end_date,
                }
            },
            'summaries': summaries,
            'total_feature_count': count
        }
        return metadata
