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
from functools import cached_property
from typing import Optional, List, Mapping, Any
from typing import Tuple

from geojson.geometry import Geometry
from xcube_geodb.core.geodb import GeoDBClient

from .vectorcube_provider import GeoDBProvider


class DataSource(abc.ABC):

    @abc.abstractmethod
    def get_values(self) -> List[Geometry]:
        pass


class GeoDBVectorSource(DataSource):

    def __init__(self, config: Mapping[str, Any]):
        self.config = config

    @cached_property
    def geodb(self) -> GeoDBClient:
        assert self.config
        api_config = self.config['geodb_openeo']
        return GeoDBProvider.create_geodb_client(api_config)
