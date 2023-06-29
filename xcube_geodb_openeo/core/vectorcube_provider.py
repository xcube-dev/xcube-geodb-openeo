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
import os
from functools import cached_property
from typing import Dict, Tuple, Optional, List, Mapping, Any

import shapely.geometry
import shapely.wkt
from geopandas import GeoDataFrame
from pandas import DataFrame

from .geodb_datasource import GeoDBVectorSource
from ..defaults import STAC_VERSION, STAC_EXTENSIONS

import pandas
from xcube_geodb.core.geodb import GeoDBClient, GeoDBError
from xcube.constants import LOG

from .vectorcube import VectorCube


class VectorCubeProvider(abc.ABC):

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

    @staticmethod
    def create_geodb_client(api_config: dict) -> GeoDBClient:
        server_url = api_config['postgrest_url']
        server_port = api_config['postgrest_port']
        client_id = api_config['client_id'] \
            if 'client_id' in api_config \
            else os.getenv('XC_GEODB_OPENEO_CLIENT_ID')
        client_secret = api_config['client_secret'] \
            if 'client_secret' in api_config \
            else os.getenv('XC_GEODB_OPENEO_CLIENT_SECRET')
        auth_domain = api_config['auth_domain']

        return GeoDBClient(
            server_url=server_url,
            server_port=server_port,
            client_id=client_id,
            client_secret=client_secret,
            auth_aud=auth_domain
        )

    @cached_property
    def geodb(self) -> GeoDBClient:
        assert self.config
        api_config = self.config['geodb_openeo']
        return GeoDBProvider.create_geodb_client(api_config)

    def get_collection_keys(self) -> List[str]:
        database_names = self.geodb.get_my_databases().get('name').array
        collections = None
        for n in database_names:
            if collections is not None:
                pandas.concat([collections, self.geodb.get_my_collections(n)])
            else:
                collections = self.geodb.get_my_collections(n)
        return collections.get('collection')

    def get_vector_cube(self, collection_id: str, with_items: bool,
                        bbox: Tuple[float, float, float, float] = None,
                        limit: Optional[int] = None, offset: Optional[int] =
                        0) \
            -> Optional[VectorCube]:
        LOG.debug(f'Building vector cube for collection {collection_id}...')
        try:
            collection_info = self.geodb.get_collection_info(collection_id)
        except GeoDBError:
            return None

        vector_cube = VectorCube(collection_id, GeoDBVectorSource(self.config))
        time_var_name = self._get_col_name(
            collection_info, ['date', 'time', 'timestamp', 'datetime'])
        vertical_dim_name = self._get_col_name(
            collection_info, ['z', 'vertical'])
        time_var_appendix = f',{time_var_name}' if time_var_name else ''
        z_dim_appendix = f',{vertical_dim_name}' if vertical_dim_name else ''
        select = f'geometry{time_var_appendix}{z_dim_appendix}'
        if bbox:
            srid = self.geodb.get_collection_srid(collection_id)
            where = f'ST_Intersects(geometry, ST_GeomFromText(\'POLYGON((' \
                    f'{bbox[0]},{bbox[1]},' \
                    f'{bbox[0]},{bbox[3]},' \
                    f'{bbox[2]},{bbox[3]},' \
                    f'{bbox[2]},{bbox[1]},' \
                    f'{bbox[0]},{bbox[1]},' \
                    f'))\',' \
                    f'{srid}))'
            gdf = self.geodb.get_collection_pg(collection_id,
                                               select=select,
                                               where=where,
                                               limit=limit,
                                               offset=offset)
        else:
            gdf = self.geodb.get_collection_pg(collection_id,
                                               select=select,
                                               limit=limit, offset=offset)
        LOG.debug(f'  ...done.')
        vector_cube._vector_dim = gdf['geometry']
        vector_cube._vertical_dim = gdf[vertical_dim_name]
        vector_cube._time_dim = gdf[time_var_name]
        LOG.debug(f'  counting collection items...')
        count = self.geodb.count_collection_by_bbox(collection_id, bbox) \
            if bbox \
            else self.geodb.count_collection_rows(collection_id,
                                                  exact_count=True)
        LOG.debug(f'  ...done.')

        collection_bbox = self._get_collection_bbox(collection_id)
        properties = self.geodb.get_properties(collection_id)

        metadata = self._create_metadata(properties, collection_id,
                                         collection_bbox, count)

        vector_cube._metadata = metadata
        LOG.debug("...done building vector cube.")
        return vector_cube

    def _get_collection_bbox(self, collection_id: str):
        LOG.debug(f'    starting to get collection bbox...')
        collection_bbox = self.geodb.get_collection_bbox(collection_id)
        if collection_bbox:
            collection_bbox = self._transform_bbox_crs(collection_bbox,
                                                       collection_id)
        if not collection_bbox:
            collection_bbox = self.geodb.get_collection_bbox(collection_id,
                                                             exact=True)
            if collection_bbox:
                collection_bbox = self._transform_bbox_crs(collection_bbox,
                                                           collection_id)

        LOG.debug(f'    ...done getting collection bbox.')
        return collection_bbox

    def _transform_bbox(self, collection_id: str,
                        bbox: Tuple[float, float, float, float],
                        crs: int) -> Tuple[float, float, float, float]:
        srid = self.geodb.get_collection_srid(collection_id)
        if srid == crs:
            return bbox
        return self.geodb.transform_bbox_crs(bbox, crs, srid)

    def _transform_bbox_crs(self, collection_bbox, collection_id):
        srid = self.geodb.get_collection_srid(collection_id)
        if srid is not None and srid != '4326':
            collection_bbox = self.geodb.transform_bbox_crs(
                collection_bbox,
                srid, '4326'
            )
        return collection_bbox

    @staticmethod
    def _get_col_name(collection_info: dict, possible_names: List[str])\
            -> Optional[str]:
        for key in collection_info['properties'].keys():
            if key in possible_names:
                return key
        return None

    @staticmethod
    def _create_metadata(properties: DataFrame, collection_id: str,
                         collection_bbox: Tuple[float, float, float, float],
                         count: int) -> {}:
        summaries = {
            'properties': []
        }
        for p in properties['column_name'].to_list():
            summaries['properties'].append({'name': p})
        metadata = {
            'title': collection_id,
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
