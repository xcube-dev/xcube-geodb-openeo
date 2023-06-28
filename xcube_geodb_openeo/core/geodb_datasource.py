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

import os
from functools import cached_property
from typing import Any, List
from typing import Mapping
from typing import Optional
from typing import Tuple

import pandas
from pandas import DataFrame
from xcube_geodb.core.geodb import GeoDBClient, GeoDBError
from xcube.constants import LOG

from .datasource import DataSource
from .vectorcube import VectorCube, VectorCubeBuilder


class GeoDBDataSource(DataSource):

    def __init__(self, config: Mapping[str, Any]):
        self.config = config

    @cached_property
    def geodb(self):
        assert self.config

        api_config = self.config['geodb_openeo']
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
        builder = VectorCubeBuilder(collection_id)
        builder.base_info = collection_info
        time_var_name = builder.get_time_var_name()
        query = f'select=geometry,{time_var_name}' if time_var_name \
            else 'select=geometry'
        gdf = self.geodb.get_collection(collection_id,
                                        query=query,
                                        limit=limit,
                                        offset=offset)
        if bbox:
            gdf = gdf.cx[bbox[0]:bbox[1], bbox[2]:bbox[3]]
        builder.geometries = gdf['geometry']
        builder.times = gdf[time_var_name]
        builder.count = gdf.count()
        builder.set_z_dim()
        vector_cube = builder.build()

        if with_items:
            if bbox:
                items = self.geodb.get_collection_by_bbox(collection_id, bbox,
                                                          limit=limit,
                                                          offset=offset)
            else:
                items = self.geodb.get_collection(collection_id, limit=limit,
                                                  offset=offset)

            vector_cube['total_feature_count'] = len(items)
            self.add_items_to_vector_cube(items, vector_cube)

        LOG.debug(f'    starting to get collection bbox...')
        collection_bbox = self.geodb.get_collection_bbox(collection_id)
        if collection_bbox:
            collection_bbox = self.transform_bbox_crs(collection_bbox,
                                                      collection_id)
        if not collection_bbox:
            collection_bbox = self.geodb.get_collection_bbox(collection_id,
                                                             exact=True)
            if collection_bbox:
                collection_bbox = self.transform_bbox_crs(collection_bbox,
                                                          collection_id)

        LOG.debug(f'    ...done getting collection bbox.')

        properties = self.geodb.get_properties(collection_id)

        self.add_metadata(collection_bbox, collection_id, properties,
                          None, vector_cube)
        LOG.debug("...done building vector cube.")
        return vector_cube

    def transform_bbox_crs(self, collection_bbox, collection_id):
        srid = self.geodb.get_collection_srid(collection_id)
        if srid is not None and srid != '4326':
            collection_bbox = self.geodb.transform_bbox_crs(
                collection_bbox,
                srid, '4326'
            )
        return collection_bbox

    @staticmethod
    def add_metadata(collection_bbox: Tuple, collection_id: str,
                     properties: DataFrame, version: Optional[str],
                     vector_cube: VectorCube):
        summaries = {
            'properties': []
        }
        for p in properties['column_name'].to_list():
            summaries['properties'].append({'name': p})
        vector_cube['metadata'] = {
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
            'summaries': summaries
        }
        if version:
            vector_cube['metadata']['version'] = version

    def transform_bbox(self, collection_id: str,
                       bbox: Tuple[float, float, float, float],
                       crs: int) -> Tuple[float, float, float, float]:
        srid = self.geodb.get_collection_srid(collection_id)
        if srid == crs:
            return bbox
        return self.geodb.transform_bbox_crs(bbox, crs, srid)
