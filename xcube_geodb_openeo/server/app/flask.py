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
from ...version import __version__

app = flask.Flask(
    __name__,
    instance_path=os.path.join(
        os.path.dirname(__file__), '../../..', 'instance'
    )
)

api = flask.Blueprint('api', __name__, url_prefix=API_URL_PREFIX)

ctx = AppContext(app.logger)


@api.route('/')
def get_info():
    return {
        'name': __name__,
        'version': __version__
    }


@api.route('/catalog')
def get_catalog_root():
    return catalog.get_root(
        ctx.for_request(flask.request.root_url)
    )


@api.route('/catalog/collections')
def get_catalog_collections():
    return catalog.get_collections(
        ctx.for_request(flask.request.root_url)
    )


@api.route('/catalog/collections/<string:collection_id>')
def get_catalog_collection(collection_id: str):
    return catalog.get_collection(
        ctx.for_request(flask.request.root_url),
        collection_id
    )


@api.route('/catalog/collections/<string:collection_id>/items')
def get_catalog_collection_items(collection_id: str):
    return catalog.get_collection_items(
        ctx.for_request(flask.request.root_url),
        collection_id
    )


@api.route('/catalog/collections/<string:collection_id>/'
           'items/<string:feature_id>')
def get_catalog_collection_item(collection_id: str, feature_id: str):
    return catalog.get_collection_item(
        ctx.for_request(flask.request.root_url),
        collection_id,
        feature_id
    )


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

    app.register_blueprint(api)
    app.run(host=address, port=port, debug=debug)
