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
import importlib
import importlib.resources as resources
import json
from abc import abstractmethod
from typing import Dict, List

from geopandas import GeoDataFrame
from xcube.server.api import ServerContextT

from xcube_geodb_openeo.core.vectorcube import VectorCube


class Process:
    """
    This class represents a process. It contains the metadata, and the method
    "Execute".
    Instances can be passed as parameter to Processing.
    """

    def __init__(self, metadata: Dict):
        if not metadata:
            raise ValueError('Empty processor metadata provided.')
        self._metadata = metadata
        self._parameters = {}

    @property
    def metadata(self) -> Dict:
        return self._metadata

    @property
    def parameters(self) -> Dict:
        return self._parameters

    @parameters.setter
    def parameters(self, p: dict) -> None:
        self._parameters = p

    @abstractmethod
    def execute(self, parameters: dict, ctx: ServerContextT) -> GeoDataFrame:
        pass


def read_default_processes() -> List[Process]:
    processes_specs = [j for j in resources.contents(f'{__package__}.res')
                       if j.lower().endswith('json')]
    processes = []
    for spec in processes_specs:
        with resources.open_binary(f'{__package__}.res', spec) as f:
            metadata = json.loads(f.read())
            module = importlib.import_module(metadata['module'])
            class_name = metadata['class_name']
            cls = getattr(module, class_name)
            processes.append(cls(metadata))

    return processes


class ProcessRegistry:

    @property
    def processes(self) -> List[Process]:
        return self._processes

    def __init__(self):
        self._processes = []
        self.links = []
        self._add_default_processes()
        self._add_default_links()

    def add_process(self, process: Process) -> None:
        self.processes.append(process)

    def add_link(self, link: Dict) -> None:
        self.links.append(link)

    def get_links(self) -> List:
        return self.links.copy()

    def get_file_formats(self) -> Dict:
        return {'input': {}, 'output': {}}

    def get_process(self, process_id: str) -> Process:
        for process in self.processes:
            if process.metadata['id'] == process_id:
                return process
        raise ValueError(f'Unknown process_id: {process_id}')

    def _add_default_processes(self):
        for dp in read_default_processes():
            self.add_process(dp)

    def _add_default_links(self):
        self.add_link({})


_PROCESS_REGISTRY_SINGLETON = None


def get_processes_registry(ctx: ServerContextT) -> ProcessRegistry:
    """Return the process registry singleton."""
    global _PROCESS_REGISTRY_SINGLETON
    if not _PROCESS_REGISTRY_SINGLETON:
        _PROCESS_REGISTRY_SINGLETON = ProcessRegistry()
    return _PROCESS_REGISTRY_SINGLETON


def submit_process_sync(p: Process, ctx: ServerContextT) -> GeoDataFrame:
    """
    Submits a process synchronously, and returns the result.
    :param p: The process to execute.
    :param ctx: The Server context.
    :return: processing result as geopandas object
    """
    parameters = p.parameters
    print(parameters)
    parameters['with_items'] = True
    # parameter_translator (introduce interface, we need to translate params from query params to backend params)
    return p.execute(parameters, ctx)


class LoadCollection(Process):

    def execute(self, parameters: dict, ctx: ServerContextT) -> GeoDataFrame:
        result = VectorCube()
        return result
