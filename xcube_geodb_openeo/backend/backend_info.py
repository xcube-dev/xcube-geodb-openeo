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
from ..version import __version__


def get_root(config: Config):
    return {
        'api_version': config['api_version'],
        'backend_version': __version__,
        'stac_version': config['stac_version'],
        'type': 'catalog',
        'id': 'xcube-geodb-openeo',
        'title': 'xcube geoDB for openEO',
        'description': 'tbd',
        'endpoints': [
            {'path': '/collections', 'methods': ['GET']},
            # TODO - only list endpoints, which are implemented and are
            #  fully compatible to the API specification.
        ],
        'links': [
            # TODO - this shall contain "Links related to this service,
            #  e.g. the homepage of the service provider or the terms of
            #  service."
        ]
    }


def get_well_known(config: Config):
    return {
        'versions': [
            {
                'url': config['url'],
                'api_version': config['api_version']
            }
        ]
    }