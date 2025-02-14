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
import os
import sys
from typing import Tuple, Optional

import jwt
import jwt.algorithms
import requests
from openeo.internal.graph_building import PGNode
from xcube.constants import LOG
from xcube.server.api import ApiError, ApiRequest, ApiResponse
from xcube.server.api import ApiHandler
from xcube_geodb.core.geodb import GeoDBError

from .api import api
from .context import _fix_time
from xcube_geodb_openeo.backend import capabilities
from xcube_geodb_openeo.backend import processes
from xcube_geodb_openeo.core.vectorcube import VectorCube
from xcube_geodb_openeo.defaults import (
    STAC_DEFAULT_ITEMS_LIMIT,
    STAC_MAX_ITEMS_LIMIT,
    STAC_MIN_ITEMS_LIMIT,
)


def authenticate(request: ApiRequest, response: ApiResponse) -> Optional[str]:
    tokens: Optional[Tuple[str, str, str]] = do_authenticate(request, response)
    if tokens:
        access_token, refresh_token, must_validate = tokens
    else:
        # if no authentication has been possible, a redirect has been prepared
        return None
    set_cookies(response, access_token, refresh_token)
    if must_validate:
        validate(access_token)
    return access_token


def do_authenticate(
    request: ApiRequest, response: ApiResponse
) -> Optional[Tuple[str, str, bool]]:
    """
    todo
    Our Keycloak version v15.0.2 does not support PKCE correctly. It's what we are using
    for testing and development. However, this means we cannot develop auth in the way
    that the openeo specification requests:

    A default OpenID Connect client is managed by the back-end implementer. It MUST
    be configured to be usable without a client secret, which limits its applicability
    to OpenID Connect grant types like "Authorization Code Grant with PKCE" and
    "Device Authorization Grant with PKCE"

    """

    cookie = request.headers["Cookie"] if "Cookie" in request.headers else None
    if cookie and "access_token=" in cookie:
        access_token = cookie.split(";")[0].split("=")[1]
        refresh_token = cookie.split(";")[1].split("=")[1]
        return access_token, refresh_token, False

    redirect_uri = request.url.split("?")[0]

    for index, (key, value) in enumerate(request.query.items()):
        if key == "code" or key == "session_state":
            continue
        if index == 0:
            redirect_uri += f"?{key}={value[0]}"
        else:
            redirect_uri += f"&{key}={value[0]}"

    kc_client_id = os.environ["KC_CLIENT_ID"]

    if "code" not in request.query:
        login_url = (
            f"https://kc.brockmann-consult.de/auth/realms/bc-services/"
            f"protocol/openid-connect/auth"
            f"?response_type=code"
            f"&scope=openid"
            f"&client_id={kc_client_id}"
            f"&redirect_uri={redirect_uri}"
        )
        response._handler.redirect(login_url, status=301)
        return None
    else:
        code = request.query["code"][0]
        kc_client_secret = os.environ["KC_CLIENT_SECRET"]
        response = requests.post(
            "https://kc.brockmann-consult.de/auth/realms/bc-services/"
            "protocol/openid-connect/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": kc_client_id,
                "client_secret": kc_client_secret,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        tokens = response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        return access_token, refresh_token, True


def set_cookies(response: ApiResponse, access_token: str, refresh_token: str) -> None:
    response._handler.set_cookie(
        "access_token", access_token, httponly=True, secure=True, samesite="Strict"
    )
    response._handler.set_cookie(
        "refresh_token", refresh_token, httponly=True, secure=True, samesite="Strict"
    )


def validate(access_token: str):
    KEYCLOAK_URL = "https://kc.brockmann-consult.de/auth/realms/bc-services"
    KEYCLOAK_JWKS_URL = f"{KEYCLOAK_URL}/protocol/openid-connect/certs"

    # Fetch public keys from Keycloak
    jwks = requests.get(KEYCLOAK_JWKS_URL).json()

    headers = jwt.get_unverified_header(access_token)

    public_key = None
    for key in jwks["keys"]:
        if key["kid"] == headers["kid"]:
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)

    if not public_key:
        raise Exception("Invalid token: No matching public key found")

    payload = jwt.decode(
        access_token, public_key, algorithms=["RS256"], audience="account"
    )
    return payload


@api.route("/")
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
        base_url = self.request.base_url
        self.response.finish(capabilities.get_root(self.ctx.config, base_url))


@api.route("/credentials/oidc")
class OidcHandler(ApiHandler):
    """
    Provides info about how to login.
    """

    @api.operation(operationId="list_oidc_providers")
    def get(self):
        providers = {
            "providers": [
                {
                    "id": "BC",
                    "issuer": "https://kc.brockmann-consult.de/auth/realms/bc-services",
                    "title": "BC - xcube geoDB",
                    "description": "Login with your xcube geoDB account.",
                    "scopes": ["openid"],
                }
            ]
        }
        self.response.finish(providers)


@api.route("/.well-known/openeo")
class WellKnownHandler(ApiHandler):
    """
    Lists all implemented openEO versions supported by the service provider.
    This endpoint is the Well-Known URI (see RFC 5785) for openEO.
    """

    @api.operation(operationId="connect", summary="Well-Known URI")
    def get(self):
        """
        Returns the well-known information.
        """
        self.response.finish(capabilities.get_well_known(self.ctx.config))


@api.route("/processes")
class ProcessesHandler(ApiHandler):
    """
    Lists all predefined processes and returns detailed process descriptions,
    including parameters and return values.
    """

    @api.operation(operationId="processes", summary="Listing of processes")
    def get(self):
        """
        Returns the processes information.
        """
        registry = processes.get_processes_registry()
        self.response.finish(
            {
                "processes": [p.metadata for p in registry.processes],
                "links": registry.get_links(),
            }
        )


@api.route("/file_formats")
class FormatsHandler(ApiHandler):
    """
    Lists supported input and output file formats. Input file formats specify
    which file a back-end can read from.
    Output file formats specify which file a back-end can write to.
    """

    @api.operation(
        operationId="file_formats", summary="Listing of supported file formats"
    )
    def get(self):
        """
        Returns the supported file formats.
        """
        self.response.finish(processes.get_processes_registry().get_file_formats())


@api.route("/result")
class ResultHandler(ApiHandler):
    """
    Executes a user-defined process directly (synchronously) and the result
    will be downloaded.
    """

    @api.operation(operationId="result", summary="Execute process synchronously.")
    def post(self):
        """
        Processes requested processing task and returns result.
        """

        access_token = authenticate(self.request, self.response)
        if not access_token:
            # a redirect has been prepared; initialise authentication
            return

        if not self.request.body:
            raise ApiError(
                400,
                "Request must contain body with valid process graph,"
                " see openEO specification.",
            )
        try:
            request = json.loads(self.request.body)
        except Exception as exc:
            raise ApiError(
                400,
                "Request must contain body with valid process graph,"
                " see openEO specification. Error: " + exc.args[0],
            )
        if "process" not in request:
            raise (ApiError(400, "Request body must contain parameter 'process'."))

        processing_request = request["process"]
        registry = processes.get_processes_registry()
        graph = processing_request["process_graph"]
        pg_node = PGNode.from_flat_graph(graph)
        registry.get_process(pg_node.process_id)

        nodes = []
        current_node = pg_node
        while (
            "data" in current_node.arguments
            and "from_node" in current_node.arguments["data"]
        ):
            nodes.append(current_node)
            current_node = current_node.arguments["data"]["from_node"]
        nodes.append(current_node)
        nodes.reverse()

        current_result = None
        for node in nodes:
            process = registry.get_process(node.process_id)
            expected_parameters = process.metadata["parameters"]
            process_parameters = node.arguments
            process_parameters["input"] = current_result
            process_parameters["access_token"] = access_token
            self.ensure_parameters(expected_parameters, process_parameters)
            process.parameters = process_parameters
            current_result = processes.submit_process_sync(process, self.ctx)

        current_result: VectorCube
        try:
            current_result.load_features()
        except GeoDBError as exc:
            raise ApiError(400, exc.args[0])
        final_result = current_result.to_geojson()
        self.response.finish(final_result)

    @staticmethod
    def ensure_parameters(expected_parameters, process_parameters):
        for ep in expected_parameters:
            is_optional_param = "optional" in ep and ep["optional"]
            if not is_optional_param:
                if ep["name"] not in process_parameters:
                    raise (
                        ApiError(
                            400, f"Request body must contain parameter '{ep['name']}'."
                        )
                    )


@api.route("/conformance")
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


@api.route("/collections")
@api.route("/collections/")
class CollectionsHandler(ApiHandler):
    """
    Lists available collections with at least the required information.
    """

    @api.operation(
        operationId="getCollections",
        summary="Gets metadata of all available collections",
    )
    def get(self):
        """
        Lists the available collections.

        Args:
            limit (int):  The optional limit parameter limits the number of
                          items that are presented in the response document.
            offset (int): Collections are listed starting at offset.
        """

        access_token = authenticate(self.request, self.response)
        if not access_token:
            # a redirect has been prepared; initialise authentication
            return

        limit = _get_limit(self.request)
        offset = _get_offset(self.request)
        base_url = self.request.base_url
        self.ctx.get_collections(access_token, base_url, limit, offset)
        self.response.finish(self.ctx.collections)


@api.route("/collections/{collection_id}")
@api.route("/collections/{collection_id}/")
class CollectionHandler(ApiHandler):
    """
    Lists all information about a specific collection specified by the
    identifier collection_id.
    """

    def get(self, collection_id: str):
        """
        Lists the collection information.
        """
        if "~" not in collection_id:
            self.response.set_status(404, f"Collection {collection_id} does not exist")
            return

        access_token = authenticate(self.request, self.response)
        if not access_token:
            # a redirect has been prepared; initialise authentication
            return

        base_url = self.request.base_url
        db = collection_id.split("~")[0]
        name = collection_id.split("~")[1]
        collection = self.ctx.get_collection(
            access_token, base_url, (db, name), True, True
        )
        if collection:
            self.response.finish(collection)
        else:
            self.response.set_status(404, f"Collection {collection_id} does not exist")


@api.route("/collections/{collection_id}/items")
@api.route("/collections/{collection_id}/items/")
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

        access_token = authenticate(self.request, self.response)
        if not access_token:
            # a redirect has been prepared; initialise authentication
            return

        limit = _get_limit(self.request, STAC_DEFAULT_ITEMS_LIMIT)
        limit = STAC_MAX_ITEMS_LIMIT if limit > STAC_MAX_ITEMS_LIMIT else limit
        limit = STAC_MIN_ITEMS_LIMIT if limit < STAC_MIN_ITEMS_LIMIT else limit
        offset = _get_offset(self.request)
        bbox = _get_bbox(self.request)
        base_url = self.request.base_url
        db = collection_id.split("~")[0]
        name = collection_id.split("~")[1]
        items = self.ctx.get_collection_items(
            access_token, base_url, (db, name), limit, offset, bbox
        )
        self.response.finish(items, content_type="application/geo+json")


@api.route("/collections/{collection_id}/items/{item_id}")
class FeatureHandler(ApiHandler):
    """
    Fetch a single item.
    """

    def get(self, collection_id: str, item_id: str):
        """
        Returns the feature.
        """

        access_token = authenticate(self.request, self.response)
        if not access_token:
            # a redirect has been prepared; initialise authentication
            return

        feature_id = item_id
        db = collection_id.split("~")[0]
        name = collection_id.split("~")[1]
        base_url = self.request.base_url
        try:
            feature = self.ctx.get_collection_item(
                access_token, base_url, (db, name), feature_id
            )
        except GeoDBError as e:
            if "does not exist" in e.args[0]:
                LOG.warning(f"Not existing feature with id {feature_id} requested.")
            self.response.set_status(404, f"Feature {feature_id} does not exist")
            return

        _fix_time(feature)
        self.response.finish(feature, content_type="application/geo+json")


@api.route("/api.html")
class OpenApiHandler(ApiHandler):
    """
    Simply forwards to openapi.html
    """

    def get(self):
        self.response._handler.redirect("/openapi.html", status=301)


def _get_limit(request, default=sys.maxsize) -> int:
    limit = (
        int(request.get_query_arg("limit"))
        if request.get_query_arg("limit")
        else default
    )
    return limit


def _get_offset(request) -> int:
    return (
        int(request.get_query_arg("offset")) if request.get_query_arg("offset") else 0
    )


def _get_bbox(request):
    if request.get_query_arg("bbox"):
        bbox = str(request.get_query_arg("bbox"))
        return tuple(bbox.split(","))
    else:
        return None
