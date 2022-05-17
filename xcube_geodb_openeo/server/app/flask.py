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


import logging
import os.path

import flask

from ..api import API_URL_PREFIX
from ..config import Config
from ..context import AppContext
from ...backend import catalog
from ...backend import capabilities
from ...backend.catalog import STAC_DEFAULT_COLLECTIONS_LIMIT
from ...backend.catalog import STAC_DEFAULT_ITEMS_LIMIT


app = flask.Flask(
    __name__,
    instance_path=os.path.join(
        os.path.dirname(__file__), '../../..', 'instance'
    )
)

well_known = flask.Blueprint('well_known', __name__)
api = flask.Blueprint('api', __name__, url_prefix=API_URL_PREFIX)

ctx = AppContext(app.logger)


@well_known.route('/.well-known/openeo')
def get_well_known():
    return capabilities.get_well_known(ctx.config)


@api.route('/')
def get_info():
    return capabilities.get_root(
        ctx.config, ctx.for_request(f'{flask.request.root_url}'
                                    f'{api.url_prefix}'))


@api.route('/conformance')
def get_conformance():
    return capabilities.get_conformance()


@api.route('/collections')
def get_catalog_collections():
    limit = int(flask.request.args['limit']) \
        if 'limit' in flask.request.args else STAC_DEFAULT_COLLECTIONS_LIMIT
    offset = int(flask.request.args['offset']) \
        if 'offset' in flask.request.args else 0
    request_ctx = ctx.for_request(f'{flask.request.root_url}{api.url_prefix}')
    return catalog.get_collections(request_ctx,
                                   request_ctx.get_url('/collections'),
                                   limit, offset)


@api.route('/collections/<string:collection_id>')
def get_catalog_collection(collection_id: str):
    return catalog.get_collection(ctx.for_request(f'{flask.request.root_url}'
                                                  f'{api.url_prefix}'),
                                  collection_id)


@api.route('/collections/<string:collection_id>/items')
def get_catalog_collection_items(collection_id: str):
    limit = int(flask.request.args['limit']) \
        if 'limit' in flask.request.args else STAC_DEFAULT_ITEMS_LIMIT
    offset = int(flask.request.args['offset']) \
        if 'offset' in flask.request.args else 0
    # sample query parameter: bbox=160.6,-55.95,-170,-25.89
    if 'bbox' in flask.request.args:
        query_bbox = str(flask.request.args['bbox'])
        bbox = tuple(query_bbox.split(','))
    else:
        bbox = None
    return catalog.get_collection_items(
        ctx.for_request(f'{flask.request.root_url}'
                        f'{api.url_prefix}'),
        collection_id, limit, offset, bbox
    )


@api.route('/collections/<string:collection_id>/'
           'items/<string:feature_id>')
def get_catalog_collection_item(collection_id: str, feature_id: str):
    return catalog.get_collection_item(ctx.for_request(flask.request.root_url),
                                       collection_id,
                                       feature_id)


@api.route('/catalog/search')
def get_catalog_search():
    return catalog.search(
        ctx.for_request(flask.request.root_url)
    )


@api.route('/catalog/search', methods=['POST'])
def post_catalog_search():
    return catalog.search(
        ctx.for_request(flask.request.root_url)
    )


def serve(
        config: Config,
        address: str,
        port: int,
        debug: bool = False,
        verbose: bool = False,
):
    ctx.config = config
    if verbose or debug:
        ctx.logger.setLevel(logging.DEBUG)

    app.register_blueprint(well_known)
    app.register_blueprint(api)
    app.run(host=address, port=port, debug=debug)
