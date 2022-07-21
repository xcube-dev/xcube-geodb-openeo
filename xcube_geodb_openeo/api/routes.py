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
import json

from ..backend import capabilities
from ..backend import processes
from .api import api
from xcube.server.api import ApiHandler
from xcube.server.api import ApiError
from .context import STAC_DEFAULT_COLLECTIONS_LIMIT


def get_limit(request):
    limit = int(request.get_query_arg('limit')) if \
        request.get_query_arg('limit') \
        else STAC_DEFAULT_COLLECTIONS_LIMIT
    return limit


def get_offset(request):
    return int(request.get_query_arg('offset')) if \
        request.get_query_arg('offset') \
        else 0


def get_bbox(request):
    if request.get_query_arg('bbox'):
        bbox = str(request.get_query_arg('bbox'))
        return tuple(bbox.split(','))
    else:
        return None


def get_base_url(request):
    # noinspection PyProtectedMember
    base_url = f'{request._request.protocol}://' \
               f'{request._request.host}'
    return base_url


@api.route('/')
class RootHandler(ApiHandler):
    """
    Lists general information about the back-end, including which version and
    endpoints of the openEO API are supported. May also include billing
    information.
    """

    def get(self):
        """
        Information about the API version and supported endpoints / features.
        """
        base_url = get_base_url(self.request)
        self.response.finish(capabilities.get_root(self.ctx.config, base_url))


@api.route('/.well-known/openeo')
class WellKnownHandler(ApiHandler):
    """
    Lists all implemented openEO versions supported by the service provider.
    This endpoint is the Well-Known URI (see RFC 5785) for openEO.
    """

    @api.operation(operationId='connect', summary='Well-Known URI')
    def get(self):
        """
        Returns the well-known information.
        """
        self.response.finish(capabilities.get_well_known(self.ctx.config))


@api.route('/processes')
class ProcessesHandler(ApiHandler):
    """
    Lists all predefined processes and returns detailed process descriptions,
    including parameters and return values.
    """

    @api.operation(operationId='processes', summary='Listing of processes')
    def get(self):
        """
        Returns the processes information.
        """
        registry = processes.get_processes_registry()
        self.response.finish({
            'processes': [p.metadata for p in registry.processes],
            'links': registry.get_links()}
        )


@api.route('/file_formats')
class FormatsHandler(ApiHandler):
    """
    Lists supported input and output file formats. Input file formats specify which file a back-end can read from.
    Output file formats specify which file a back-end can write to.
    """

    @api.operation(operationId='file_formats', summary='Listing of supported file formats')
    def get(self):
        """
        Returns the supported file formats.
        """
        self.response.finish(processes.get_processes_registry().get_file_formats())


@api.route('/result')
class ResultHandler(ApiHandler):
    """
    Executes a user-defined process directly (synchronously) and the result will be downloaded.
    """

    @api.operation(operationId='result', summary='Execute process'
                                                 'synchronously.')
    def post(self):
        """
        Processes requested processing task and returns result.
        """
        if not self.request.body:
            raise (ApiError(400, 'Request body must contain key \'process\'.'))

        processing_request = json.loads(self.request.body)['process']
        process_id = processing_request['id']
        process_parameters = processing_request['parameters']
        registry = processes.get_processes_registry()
        process = registry.get_process(process_id)

        expected_parameters = process.metadata['parameters']
        self.ensure_parameters(expected_parameters, process_parameters)
        process.parameters = process_parameters

        result = processes.submit_process_sync(process, self.ctx)
        self.response.finish(result)

    def ensure_parameters(self, expected_parameters, process_parameters):
        for ep in expected_parameters:
            is_optional_param = 'optional' in ep and ep['optional']
            if not is_optional_param:
                if ep['name'] not in process_parameters:
                    raise (ApiError(400, f'Request body must contain parameter'
                                         f' \'{ep["name"]}\'.'))


@api.route('/conformance')
class ConformanceHandler(ApiHandler):
    """
    Lists all conformance classes specified in OGC standards that the server
    conforms to.
    """

    def get(self):
        """
        Lists the conformance classes.
        """
        self.response.finish(capabilities.get_conformance())


@api.route('/collections')
class CollectionsHandler(ApiHandler):
    """
    Lists available collections with at least the required information.
    """

    @api.operation(operationId='getCollections',
                   summary='Gets metadata of all available collections')
    def get(self):
        """
        Lists the available collections.

        Args:
            limit (int):  The optional limit parameter limits the number of
                          items that are presented in the response document.
            offset (int): Collections are listed starting at offset.
        """
        limit = get_limit(self.request)
        offset = get_offset(self.request)
        base_url = get_base_url(self.request)
        if not self.ctx.collections:
            self.ctx.fetch_collections(base_url, limit, offset)
        self.response.finish(self.ctx.collections)


@api.route('/collections/{collection_id}')
class CollectionHandler(ApiHandler):
    """
    Lists all information about a specific collection specified by the
    identifier collection_id.
    """

    def get(self, collection_id: str):
        """
        Lists the collection information.
        """
        base_url = get_base_url(self.request)
        collection = self.ctx.get_collection(base_url, collection_id)
        self.response.finish(collection)


@api.route('/collections/{collection_id}/items')
class CollectionItemsHandler(ApiHandler):
    """
    Get features of the feature collection with id collectionId.
    """

    # noinspection PyIncorrectDocstring
    def get(self, collection_id: str):
        """
        Returns the features.

        Args:
            limit (int):  Optional, limits the number of items presented in
            the response document.
            offset (int): Optional, collections are listed starting at offset.
            bbox (array of numbers): Only features that intersect the bounding
                box are selected. Example: bbox=160.6,-55.95,-170,-25.89
        """
        limit = get_limit(self.request)
        offset = get_offset(self.request)
        bbox = get_bbox(self.request)
        base_url = get_base_url(self.request)
        items = self.ctx.get_collection_items(base_url, collection_id,
                                              limit, offset, bbox)
        self.response.finish(items)


@api.route('/collections/{collection_id}/items/{feature_id}')
class FeatureHandler(ApiHandler):
    """
    Fetch a single feature.
    """

    def get(self, collection_id: str, feature_id: str):
        """
        Returns the feature.
        """
        base_url = get_base_url(self.request)
        feature = self.ctx.get_collection_item(base_url, collection_id,
                                               feature_id)
        self.response.finish(feature)
