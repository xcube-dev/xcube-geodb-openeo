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

from ..server.config import Config
from ..server.context import RequestContext
from ..version import __version__

'''
Implements the endpoints listed under
https://openeo.org/documentation/1.0/developers/api/reference.html#tag/Capabilities 
'''


def get_root(config: Config, ctx: RequestContext):
    return {
        'api_version': config['API_VERSION'],
        'backend_version': __version__,
        'stac_version': config['STAC_VERSION'],
        'type': 'catalog',
        "id": config['SERVER_ID'],
        "title": config['SERVER_TITLE'],
        "description": config['SERVER_DESCRIPTION'],
        'endpoints': [
            {'path': '/collections', 'methods': ['GET']},
            # TODO - only list endpoints, which are implemented and are
            #  fully compatible to the API specification.
        ],
        "links": [  # todo - links are incorrect
            {
                "rel": "self",
                "href": ctx.get_url('/'),
                "type": "application/json",
                "title": "this document"
            },
            {
                "rel": "service-desc",
                "href": ctx.get_url('/api'),
                "type": "application/vnd.oai.openapi+json;version=3.0",
                "title": "the API definition"
            },
            {
                "rel": "service-doc",
                "href": ctx.get_url('/api.html'),
                "type": "text/html",
                "title": "the API documentation"
            },
            {
                "rel": "conformance",
                "href": ctx.get_url('/conformance'),
                "type": "application/json",
                "title": "OGC API conformance classes"
                         " implemented by this server"
            },
            {
                "rel": "data",
                "href": ctx.get_url('/collections'),
                "type": "application/json",
                "title": "Information about the feature collections"
            },
            {
                "rel": "search",
                "href": ctx.get_url('/search'),
                "type": "application/json",
                "title": "Search across feature collections"
            }
        ]
    }


def get_well_known(config: Config):
    return {
        'versions': [
            {
                'url': config['SERVER_URL'],
                'api_version': config['API_VERSION']
            }
        ]
    }


# noinspection PyUnusedLocal
def get_conformance():
    return {
        "conformsTo": [
            # TODO: fix this list so it becomes true
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/html",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson"
        ]
    }