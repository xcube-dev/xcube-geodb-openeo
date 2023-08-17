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
from datetime import datetime
from functools import cached_property
from typing import Any, Optional, Tuple, Dict
from typing import List

from geojson import FeatureCollection
from geojson.geometry import Geometry

from xcube_geodb_openeo.core.geodb_datasource import DataSource, Feature
from xcube_geodb_openeo.core.tools import Cache
from xcube_geodb_openeo.defaults import STAC_DEFAULT_ITEMS_LIMIT


class VectorCube:

    """
    Representation of a VectorCube, according to
    https://r-spatial.org/r/2022/09/12/vdc.html.

    When is a geoDB table column a dimension?
    In a vector cube, the geometry always is a dimensions. If the geometry in
    the geoDB is 3-dimensional (is that possible anyway?), we have to split
    that into a 2d geometry and an additional vertical dimension.
    The time column translates to a dimension as well.
    Other columns (say, chl_mean) never translate to a dimension; rather, each
    position in the cube (given by geometry, maybe z, and time) contains an
    array of unspecific type. Thus, we do not have additional dimensions for
    geoDB tables.
    It could be useful to make a column a dimension, if the column changes
    its value only if all combinations of values of the other dimensions
    change. Wavelength is a good example: for 440nm, there are entries for all
    geometries and datetimes, and for 550nm, there are others.
    However, detecting this from a table is hard, therefore we don't do it.

    The actual values within this VectorCube are provided by a dask Dataframe.
    """

    def __init__(self, collection_id: Tuple[str, str],
                 datasource: DataSource) -> None:
        (self._database, self._id) = collection_id
        self._datasource = datasource
        self._metadata = {}
        self._feature_cache = Cache(1000)
        self._vector_dim_cache = Cache(100)
        self._vertical_dim_cache = Cache(1000)
        self._time_dim_cache = Cache(1000)
        self._version = ''
        self._bbox = None
        self._geometry_types = None
        self._vector_dim = []
        self._vertical_dim = []
        self._time_dim = []

    @cached_property
    def id(self) -> str:
        return self._database + '~' + self._id

    @cached_property
    def srid(self) -> str:
        return str(self._datasource.get_srid())

    @cached_property
    def feature_count(self) -> int:
        return self._datasource.get_feature_count()

    def get_vector_dim(
            self, bbox: Optional[Tuple[float, float, float, float]] = None) \
            -> List[Geometry]:
        """
        Represents the vector dimension of the vector cube. By definition,
        vector data cubes have (at least) a single spatial dimension.

        What is a geometry dim?
            Explicitly defined: a list of all the different values, e.g.  [POINT(5 7), POINT(1.3 4), POINT(8 3)]
            Implicitly defined: simply a name, which can be used to get the values from a dict or something
            -> we define it explicitly
        # shall we support multiple geometry dimensions?
            - check openEO requirements/specifications on this
        # shall we return GeoJSON? Or CovJSON?
            - use what's best suited for internal use
            - go with GeoJSON first
        # no need for lazy loading: we want to read the geometries at once as
            they form the cube. So they can be read while building the cube.

        :return: list of geojson geometries, which all together form the
        vector dimension
        """
        global_key = 'GLOBAL'
        if bbox and bbox in self._vector_dim_cache.get_keys():
            return self._vector_dim_cache.get(bbox)
        if not bbox and global_key in self._vector_dim_cache.get_keys():
            return self._vector_dim_cache.get(global_key)
        vector_dim = self._datasource.get_vector_dim(bbox)
        self._vector_dim_cache.insert(bbox if bbox else global_key, vector_dim)
        return vector_dim

    def get_vertical_dim(
            self,
            bbox: Optional[Tuple[float, float, float, float]] = None) \
            -> List[Any]:
        """
        Represents the vertical geometry dimension of the vector cube, if it
        exists. Returns the explicit list of dimension values. If the vector
        cube does not have a vertical dimension, returns an empty list.
        :return: list of dimension values, typically a list of float values.
        """
        global_key = 'GLOBAL'
        if bbox and bbox in self._vertical_dim_cache.get_keys():
            return self._vertical_dim_cache.get(bbox)
        if not bbox and global_key in self._vertical_dim_cache.get_keys():
            return self._vertical_dim_cache.get(global_key)
        v_dim = self._datasource.get_vertical_dim(bbox)
        self._vertical_dim_cache.insert(bbox if bbox else global_key, v_dim)
        return v_dim

    def get_time_dim(
            self, bbox: Optional[Tuple[float, float, float, float]] = None) \
            -> List[datetime]:
        """
        Returns the time dimension of the vector cube as an explicit list of
        datetime objects. If the vector cube does not have a time dimension,
        an empty list is returned.
        """
        global_key = 'GLOBAL'
        if bbox and bbox in self._time_dim_cache.get_keys():
            return self._time_dim_cache.get(bbox)
        if not bbox and global_key in self._time_dim_cache.get_keys():
            return self._time_dim_cache.get(global_key)
        time_dim = self._datasource.get_time_dim(bbox)
        self._time_dim_cache.insert(bbox if bbox else global_key, time_dim)
        return time_dim

    def get_feature(self, feature_id: str) -> Feature:
        for key in self._feature_cache.get_keys():
            for feature in self._feature_cache.get(key):
                if feature['id'] == feature_id:
                    return feature
        feature = self._datasource.load_features(feature_id=feature_id)[0]
        self._feature_cache.insert(feature_id, [feature])
        return feature

    def load_features(self, limit: int = STAC_DEFAULT_ITEMS_LIMIT,
                      offset: int = 0,
                      with_stac_info: bool = True) -> List[Feature]:
        key = (limit, offset)
        if key in self._feature_cache.get_keys():
            return self._feature_cache.get(key)
        features = self._datasource.load_features(limit, offset,
                                                  None, with_stac_info)
        self._feature_cache.insert(key, features)
        return features

    def get_bbox(self) -> Optional[Tuple[float, float, float, float]]:
        if self._bbox:
            return self._bbox
        self._bbox = self._datasource.get_vector_cube_bbox()
        return self._bbox

    def get_geometry_types(self) -> List[str]:
        if self._geometry_types:
            return self._geometry_types
        self._geometry_types = self._datasource.get_geometry_types()
        return self._geometry_types

    def get_metadata(self, full: bool = False) -> Dict:
        return self._datasource.get_metadata(full)

    def to_geojson(self) -> FeatureCollection:
        return FeatureCollection(self.load_features(
            self.feature_count, 0, False))
