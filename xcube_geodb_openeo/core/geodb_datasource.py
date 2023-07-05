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
from datetime import datetime
from functools import cached_property
from typing import List, Mapping, Any, Optional, Tuple, Dict

import dateutil.parser
import shapely
from geojson.geometry import Geometry
from pandas import Series
from xcube.constants import LOG
from xcube_geodb.core.geodb import GeoDBClient, GeoDBError

from .tools import create_geodb_client
from ..defaults import STAC_VERSION, STAC_EXTENSIONS, STAC_DEFAULT_ITEMS_LIMIT

Feature = Dict[str, Any]


class DataSource(abc.ABC):

    @abc.abstractmethod
    def get_vector_dim(self,
                       bbox: Optional[Tuple[float, float, float, float]] = None
                       ) -> List[Geometry]:
        pass

    @abc.abstractmethod
    def get_srid(self) -> int:
        pass

    @abc.abstractmethod
    def get_feature_count(self) -> int:
        pass

    @abc.abstractmethod
    def get_time_dim(
            self,
            bbox: Optional[Tuple[float, float, float, float]] = None) \
            -> Optional[List[datetime]]:
        pass

    @abc.abstractmethod
    def get_vertical_dim(
            self,
            bbox: Optional[Tuple[float, float, float, float]] = None) \
            -> Optional[List[Any]]:
        pass

    @abc.abstractmethod
    def load_features(self, limit: int = STAC_DEFAULT_ITEMS_LIMIT,
                      offset: int = 0,
                      feature_id: Optional[str] = None) -> List[Feature]:
        pass

    @abc.abstractmethod
    def get_vector_cube_bbox(self) -> Tuple[float, float, float, float]:
        pass

    @abc.abstractmethod
    def get_geometry_types(self) -> List[str]:
        pass

    @abc.abstractmethod
    def get_metadata(self, bbox: Tuple[float, float, float, float]) -> Dict:
        pass


class GeoDBVectorSource(DataSource):

    def __init__(self, config: Mapping[str, Any],
                 collection_id: Tuple[str, str]):
        self.config = config
        self.collection_id = collection_id

    @cached_property
    def geodb(self) -> GeoDBClient:
        assert self.config
        api_config = self.config['geodb_openeo']
        return create_geodb_client(api_config)

    @cached_property
    def collection_info(self):
        (db, name) = self.collection_id
        try:
            collection_info = self.geodb.get_collection_info(name, db)
        except GeoDBError:
            return None  # todo - raise meaningful error
        return collection_info

    def get_feature_count(self) -> int:
        (db, name) = self.collection_id
        LOG.debug(f'Retrieving count from geoDB...')
        count = self.geodb.count_collection_rows(name, database=db,
                                                 exact_count=True)
        LOG.debug(f'...done.')
        return count

    def get_srid(self) -> int:
        (db, name) = self.collection_id
        return int(self.geodb.get_collection_srid(name, db))

    def get_geometry_types(self) -> List[str]:
        LOG.debug(f'Loading geometry types for vector cube '
                  f'{self.collection_id} from geoDB...')
        (db, name) = self.collection_id
        return self.geodb.get_geometry_types(collection=name, aggregate=True,
                                             database=db)

    def load_features(self, limit: int = STAC_DEFAULT_ITEMS_LIMIT,
                      offset: int = 0,
                      feature_id: Optional[str] = None) -> List[Feature]:
        LOG.debug(f'Loading features of collection {self.collection_id} from '
                  f'geoDB...')
        (db, name) = self.collection_id
        select = 'id,geometry'
        time = self._get_col_name(['date', 'time', 'timestamp', 'datetime'])
        if time:
            select = f'{select},{time}'
        if feature_id:
            gdf = self.geodb.get_collection_pg(
                name, select=select, where=f'id = {feature_id}', database=db)
        else:
            gdf = self.geodb.get_collection_pg(
                name, select=select, limit=limit, offset=offset, database=db)

        features = []
        properties = list(self.collection_info['properties'].keys())

        for i, row in enumerate(gdf.iterrows()):
            bbox = gdf.bounds.iloc[i]
            coords = self._get_coords(row[1])

            feature = {
                'stac_version': STAC_VERSION,
                'stac_extensions': STAC_EXTENSIONS,
                'type': 'Feature',
                'id': str(row[1]['id']),
                'bbox': [f'{bbox["minx"]:.4f}',
                         f'{bbox["miny"]:.4f}',
                         f'{bbox["maxx"]:.4f}',
                         f'{bbox["maxy"]:.4f}'],
                'geometry': coords,
                'properties': properties
            }
            if time:
                feature['datetime'] = row[1][time]
            features.append(feature)
        LOG.debug('...done.')
        return features

    def get_vector_dim(self,
                       bbox: Optional[Tuple[float, float, float, float]] = None
                       ) -> List[Geometry]:
        select = f'geometry'
        if bbox:
            LOG.debug(f'Loading geometry for {self.collection_id} from geoDB...')
            gdf = self._fetch_from_geodb(select, bbox)
        else:
            LOG.debug(f'Loading global geometry for {self.collection_id} '
                      f'from geoDB...')
            (db, name) = self.collection_id
            gdf = self.geodb.get_collection_pg(
                name, select=select, group=select, database=db)
        LOG.debug('...done.')

        return list(gdf['geometry'])

    def get_time_dim(
            self, bbox: Optional[Tuple[float, float, float, float]] = None) \
            -> Optional[List[datetime]]:
        select = self._get_col_name(['date', 'time', 'timestamp', 'datetime'])
        if not select:
            return None
        if bbox:
            gdf = self._fetch_from_geodb(select, bbox)
        else:
            (db, name) = self.collection_id
            gdf = self.geodb.get_collection_pg(
                name, select=select, database=db)

        return [dateutil.parser.parse(d) for d in gdf[select]]

    def get_vertical_dim(
            self, bbox: Optional[Tuple[float, float, float, float]] = None) \
            -> Optional[List[Any]]:
        select = self._get_col_name(['z', 'vertical'])
        if not select:
            return None
        if bbox:
            gdf = self._fetch_from_geodb(select, bbox)
        else:
            (db, name) = self.collection_id
            gdf = self.geodb.get_collection_pg(
                name, select=select, database=db)

        return gdf[select]

    def get_vector_cube_bbox(self) -> Tuple[float, float, float, float]:
        (db, name) = self.collection_id
        LOG.debug(f'Loading collection bbox for {self.collection_id} from '
                  f'geoDB...')
        vector_cube_bbox = self.geodb.get_collection_bbox(name, database=db)
        if vector_cube_bbox:
            vector_cube_bbox = self._transform_bbox_crs(vector_cube_bbox,
                                                        name, db)
        if not vector_cube_bbox:
            vector_cube_bbox = self.geodb.get_collection_bbox(name, db,
                                                              exact=True)
            if vector_cube_bbox:
                vector_cube_bbox = self._transform_bbox_crs(vector_cube_bbox,
                                                            name, db)

        LOG.debug(f'...done.')
        return vector_cube_bbox

    def get_metadata(self, bbox: Tuple[float, float, float, float]) -> Dict:
        (db, name) = self.collection_id
        col_names = list(self.collection_info['properties'].keys())
        time_column = self._get_col_name(
            ['date', 'time', 'timestamp', 'datetime'])
        if time_column:
            LOG.debug(f'Loading time interval for {self.collection_id} from '
                      f'geoDB...')
            earliest = self.geodb.get_collection_pg(
                name, select=time_column,
                order=time_column, limit=1,
                database=db)[time_column][0]
            earliest = dateutil.parser.parse(earliest).isoformat()
            latest = self.geodb.get_collection_pg(
                name, select=time_column,
                order=f'{time_column} DESC',
                limit=1, database=db)[time_column][0]
            latest = dateutil.parser.parse(latest).isoformat()
            LOG.debug(f'...done.')
        else:
            earliest, latest = None, None

        metadata = {
            'title': f'{name}',
            'extent': {
                'spatial': {
                    'bbox': [bbox],
                },
                'temporal': {
                    'interval': [[earliest, latest]]
                }
            },
            'summaries': {
                'column_names': col_names
            },
        }
        return metadata

    def _transform_bbox(self, collection_id: Tuple[str, str],
                        bbox: Tuple[float, float, float, float],
                        crs: int) -> Tuple[float, float, float, float]:
        (db, name) = collection_id
        srid = self.geodb.get_collection_srid(name, database=db)
        if srid == crs:
            return bbox
        return self.geodb.transform_bbox_crs(bbox, crs, srid)

    def _transform_bbox_crs(self, collection_bbox, name: str, db: str):
        srid = self.geodb.get_collection_srid(name, database=db)
        if srid is not None and srid != '4326':
            collection_bbox = self.geodb.transform_bbox_crs(
                collection_bbox,
                srid, '4326'
            )
        return collection_bbox

    def _get_col_name(self, possible_names: List[str]) -> Optional[str]:
        for key in self.collection_info['properties'].keys():
            if key in possible_names:
                return key
        return None

    def _fetch_from_geodb(self, select: str,
                          bbox: Tuple[float, float, float, float]):
        (db, name) = self.collection_id
        srid = self.geodb.get_collection_srid(name, database=db)
        where = f'ST_Intersects(geometry, ST_GeomFromText(\'POLYGON((' \
                f'{bbox[0]},{bbox[1]},' \
                f'{bbox[0]},{bbox[3]},' \
                f'{bbox[2]},{bbox[3]},' \
                f'{bbox[2]},{bbox[1]},' \
                f'{bbox[0]},{bbox[1]},' \
                f'))\',' \
                f'{srid}))'
        return self.geodb.get_collection_pg(name,
                                            select=select,
                                            where=where,
                                            group=select,
                                            database=db)

    @staticmethod
    def _get_coords(feature: Series) -> Dict:
        geometry = feature['geometry']
        feature_wkt = shapely.wkt.loads(geometry.wkt)
        return shapely.geometry.mapping(feature_wkt)
