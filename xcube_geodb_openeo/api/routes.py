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
from ..backend import capabilities
from .api import api
from xcube.server.api import ApiHandler
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
        self.response.finish(capabilities.get_well_known(self.config))


@api.route('/collections')
class CollectionsHandler(ApiHandler):
    """
    Lists available collections with at least the required information.
    """

    @api.operation(operationId='getCollections', summary='Gets metadata of ')
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
        base_url = f'{self.request._request.protocol}://' \
                   f'{self.request._request.host}'
        self.ctx.request = self.request
        if not self.ctx.collections:
            self.ctx.fetch_collections(self.ctx, base_url, limit, offset)
        self.response.finish(self.ctx.collections)


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


@api.route('/collections/<string:collection_id>')
class CollectionHandler(ApiHandler):
    """
    Lists all information about a specific collection specified by the
    identifier collection_id.
    """

    def get(self):
        """
        Lists the collection information.
        """
        # todo - collection_id is not a query argument, but a path argument.
        # Change as soon as Server NG allows
        collection_id = self.request.get_query_arg('collection_id')
        base_url = f'{self.request._request.protocol}://' \
                   f'{self.request._request.host}'
        collection = self.ctx.get_collection(self.ctx, base_url, collection_id)
        self.response.finish(collection)


@api.route('/collections/<string:collection_id>/items')
class CollectionItemsHandler(ApiHandler):
    """
    Get features of the feature collection with id collectionId.
    """

    # noinspection PyIncorrectDocstring
    def get(self):
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

        # todo - collection_id is not a query argument, but a path argument.
        # Change as soon as Server NG allows
        collection_id = self.request.get_query_arg('collection_id')

        base_url = f'{self.request._request.protocol}://' \
                   f'{self.request._request.host}'
        items = self.ctx.get_collection_items(self.ctx, base_url, collection_id,
                                             limit, offset, bbox)
        self.response.finish(items)


@api.route('/collections/<string:collection_id>/'
           'items/<string:feature_id>')
class FeatureHandler(ApiHandler):
    """
    Fetch a single feature.
    """
    def get(self):
        """
        Returns the feature.
        """

        # todo - collection_id is not a query argument, but a path argument.
        # Change as soon as Server NG allows
        collection_id = self.request.get_query_arg('collection_id')
        feature_id = self.request.get_query_arg('feature_id')

        feature = self.ctx.get_collection_item(self.ctx, collection_id,
                                               feature_id)
        self.response.finish(feature)
