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
import importlib
import logging
from typing import Sequence

from ..core.vectorcube import VectorCube
from ..core.datastore import DataStore
from ..server.config import Config


class Context(abc.ABC):

    @property
    @abc.abstractmethod
    def config(self) -> Config:
        pass

    @property
    @abc.abstractmethod
    def collection_ids(self) -> Sequence[str]:
        pass

    @abc.abstractmethod
    def get_vector_cube(self, collection_id: str) -> VectorCube:
        pass

    @property
    @abc.abstractmethod
    def logger(self) -> logging.Logger:
        pass

    def for_request(self, root_url: str) -> 'RequestContext':
        return RequestContext(self, root_url)


class AppContext(Context):
    def __init__(self, logger: logging.Logger):
        self._config = None
        self._logger = logger

    @property
    def config(self) -> Config:
        assert self._config is not None
        return self._config

    @config.setter
    def config(self, config: Config):
        assert isinstance(config, dict)
        self._config = dict(config)

    @property
    def data_store(self) -> DataStore:
        if not self.config:
            raise RuntimeError('config not set')
        data_store_class = self.config['datastore-class']
        data_store_module = data_store_class[:data_store_class.rindex('.')]
        class_name = data_store_class[data_store_class.rindex('.') + 1:]
        module = importlib.import_module(data_store_module)
        cls = getattr(module, class_name)
        return cls()

    @property
    def collection_ids(self) -> Sequence[str]:
        # TODO: fetch from geoDB
        return tuple(self.data_store.get_collection_keys())

    def get_vector_cube(self, collection_id: str) -> VectorCube:
        return self.data_store.get_vector_cube(collection_id)

    @property
    def logger(self) -> logging.Logger:
        return self._logger


class RequestContext(Context):

    def __init__(self, ctx: Context, root_url: str):
        self._ctx = ctx
        self._root_url = root_url

    @property
    def root_url(self) -> str:
        return self._root_url

    def get_url(self, path: str):
        return f'{self._root_url}/{path}'

    @property
    def config(self) -> Config:
        return self._ctx.config

    @property
    def collection_ids(self) -> Sequence[str]:
        return self._ctx.collection_ids

    def get_vector_cube(self, collection_id: str) -> VectorCube:
        return self._ctx.get_vector_cube(collection_id)

    @property
    def logger(self) -> logging.Logger:
        return self._ctx.logger
