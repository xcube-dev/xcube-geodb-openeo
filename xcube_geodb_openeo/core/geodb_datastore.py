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

from functools import cached_property
from typing import Tuple

from .datastore import DataStore
from xcube_geodb.core.geodb import GeoDBClient

from .vectorcube import VectorCube
from ..server.config import Config


class GeoDBDataStore(DataStore):

    def __init__(self, config: Config):
        self.config = config

    @cached_property
    def geodb(self):
        assert self.config

        server_url = self.config['postgrest_url']
        server_port = self.config['postgrest_port']
        client_id = self.config['client_id']
        client_secret = self.config['client_secret']
        auth_domain = self.config['auth_domain']

        return GeoDBClient(
            server_url=server_url,
            server_port=server_port,
            client_id=client_id,
            client_secret=client_secret,
            auth_aud=auth_domain
        )

    def get_collection_keys(self):
        database_names = self.geodb.get_my_databases().get('name').array
        collections = None
        for n in database_names:
            if collections:
                collections.concat(self.geodb.get_my_collections(n))
            else:
                collections = self.geodb.get_my_collections(n)
        return collections.get('collection')

    def get_vector_cube(self, collection_id: str, limit: int, offset: int,
                        with_items: bool,
                        bbox: Tuple[float, float, float, float]) \
            -> VectorCube:
        vector_cube = self.geodb.get_collection_info(collection_id)
        vector_cube['id'] = collection_id
        vector_cube['features'] = []
        if bbox:
            vector_cube['total_feature_count'] = \
                self.geodb.count_collection_by_bbox(collection_id, bbox)
            items = self.geodb.get_collection_by_bbox(collection_id, bbox,
                                                      limit=limit,
                                                      offset=offset)
        else:
            vector_cube['total_feature_count'] = \
                self.geodb.count_collection_by_bbox(collection_id,
                                                    (-180, 90, 180, -90))
            items = self.geodb.get_collection(collection_id, limit=limit,
                                              offset=offset)

        if with_items:
            self.add_items_to_vector_cube(items, vector_cube, self.config)

        return vector_cube
