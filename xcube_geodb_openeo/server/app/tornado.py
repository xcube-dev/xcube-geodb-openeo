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
from typing import Dict, Type, Callable, Optional, Any

import tornado
import tornado.escape
import tornado.ioloop
import tornado.web

from xcube_geodb_openeo.backend import catalog
from ..api import API_URL_PREFIX
from ..config import Config
from ..context import AppContext
from ..context import RequestContext
from ...backend import capabilities

RequestHandlerType = Type[tornado.web.RequestHandler]


class App:
    """Defines a decorator that makes routing easier."""

    def __init__(self):
        self.handlers = []

    def route(self,
              pattern: str,
              kwargs: Optional[Dict[str, Any]] = None,
              name: Optional[str] = None,
              prefix: str = API_URL_PREFIX) \
            -> Callable[[RequestHandlerType], RequestHandlerType]:
        """Allows us to decorate Tornado handlers like Flask does."""

        def decorator(cls: RequestHandlerType):
            prefixed_pattern = prefix + pattern
            print(prefixed_pattern)
            url_pattern = self.url_pattern(prefixed_pattern)
            self.handlers.append(
                tornado.web.url(url_pattern,
                                cls,
                                kwargs=kwargs,
                                name=name)
            )
            return cls

        return decorator

    @classmethod
    def url_pattern(cls, pattern: str):
        """Convert a string *pattern* where any occurrences of ``{NAME}``
        are replaced by an equivalent regex expression which will assign
        matching character groups to NAME. Characters match until
        one of the RFC 2396 reserved characters is found or the end of the
        *pattern* is reached.

        RFC 2396 Uniform Resource Identifiers (URI): Generic Syntax lists
        the following reserved characters::

            reserved    = ";" | "/" | "?" | ":" | "@" | "&" | "=" |
                          "+" | "$" | ","

        :param pattern: URL pattern
        :return: equivalent regex pattern
        :raise ValueError: if *pattern* is invalid
        """
        name_pattern = r'(?P<%s>[^\;\/\?\:\@\&\=\+\$\,]+)'
        results = []
        for i, p in enumerate(pattern.split('{')):
            closing = p.split('}')
            if i == 0:
                if len(closing) > 1:
                    raise ValueError('closing "}" without opening "{"')
                results.append(p)
            else:
                if len(closing) < 2:
                    raise ValueError('closing "}" missing after opening "{"')
                if len(closing) > 2:
                    raise ValueError('closing "}" without opening "{"')
                name = closing[0]
                if not name.isidentifier():
                    raise ValueError(
                        'NAME in "{NAME}" must be a valid identifier,'
                        ' but got "%s"' % name
                    )
                results.append(name_pattern % name)
                results.append(closing[1])
        return ''.join(results)

    @classmethod
    def to_int(cls, name: str, value: str) -> int:
        try:
            return int(value)
        except ValueError:
            raise tornado.web.HTTPError(403, f'integer expected for {name!r}')


app = App()


def _get_request_ctx(handler: tornado.web.RequestHandler) -> RequestContext:
    request = handler.request
    root_url = request.protocol + "://" + request.host
    return ctx.for_request(root_url)


# ========================================================
# Add handlers
# ========================================================

# noinspection PyAbstractClass
class BaseHandler(tornado.web.RequestHandler):

    def set_default_headers(self):
        """Overridden to naively enable CORS."""
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers",
                        "x-requested-with")
        self.set_header("Access-Control-Allow-Methods",
                        "POST,PUT,GET,DELETE,OPTIONS")

    # noinspection PyUnusedLocal
    def options(self, *args):
        """Implemented to always return status 204 (for pre-flight check)."""
        self.set_status(204)
        self.finish()

    def write_error(self, status_code: int, **kwargs: Any) -> None:
        """Overridden to always return a JSON error object."""
        error = dict(status=status_code)

        reason = kwargs.get("reason")
        if reason is not None:
            error["reason"] = reason

        data = kwargs.get("data")
        if data is not None:
            error["data"] = data

        exc_info = kwargs.get("exc_info")
        if exc_info is not None:
            import traceback
            traceback.format_exception(*kwargs["exc_info"])
            error["traceback"] = list(traceback.format_exception(*exc_info))

        self.finish(error)


# noinspection PyAbstractClass,PyMethodMayBeStatic
@app.route('/')
class MainHandler(BaseHandler):
    async def get(self):
        return await self.finish(
            capabilities.get_root(ctx.config, _get_request_ctx(self))
        )


# noinspection PyAbstractClass,PyMethodMayBeStatic
@app.route('/.well-known/openeo', prefix='')
class MainHandler(BaseHandler):
    async def get(self):
        return await self.finish(capabilities.get_well_known(ctx.config))


# noinspection PyAbstractClass,PyMethodMayBeStatic
@app.route('/conformance')
class CatalogConformanceHandler(BaseHandler):
    async def get(self):
        return await self.finish(capabilities.get_conformance())


# noinspection PyAbstractClass,PyMethodMayBeStatic
@app.route("/collections")
class CatalogCollectionsHandler(BaseHandler):
    async def get(self):
        from xcube_geodb_openeo.backend import catalog
        return await self.finish(catalog.get_collections(
            _get_request_ctx(self)
        ))


# noinspection PyAbstractClass,PyMethodMayBeStatic
@app.route("/collections/{collection_id}")
class CatalogCollectionHandler(BaseHandler):
    async def get(self, collection_id: str):
        from xcube_geodb_openeo.backend import catalog
        return await self.finish(catalog.get_collection(
            _get_request_ctx(self),
            collection_id
        ))


# noinspection PyAbstractClass,PyMethodMayBeStatic
@app.route("/collections/{collection_id}/items")
class CatalogCollectionItemsHandler(BaseHandler):
    async def get(self, collection_id: str):
        return await self.finish(catalog.get_collection_items(
            _get_request_ctx(self),
            collection_id
        ))


# noinspection PyAbstractClass,PyMethodMayBeStatic
@app.route("/catalog/collections/{collection_id}/items/{feature_id}")
class CatalogCollectionItemHandler(BaseHandler):
    async def get(self, collection_id: str, feature_id: str):
        return await self.finish(catalog.get_collection_item(
            _get_request_ctx(self), collection_id, feature_id
        ))


# noinspection PyAbstractClass,PyMethodMayBeStatic
@app.route("/catalog/search")
class CatalogSearchHandler(BaseHandler):

    async def get(self):
        return await self.finish(catalog.search(
            _get_request_ctx(self)
        ))

    async def post(self):
        return await self.finish(catalog.search(
            _get_request_ctx(self)
        ))


ctx = AppContext(logging.getLogger('tornado'))

MultiResDatasets = Dict[str,
                        'xcube_tileserver.core.mrdataset.MultiResDataset']


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

    application = tornado.web.Application(app.handlers, debug=debug)
    application.listen(address=address, port=port)
    tornado.ioloop.IOLoop.current().start()
