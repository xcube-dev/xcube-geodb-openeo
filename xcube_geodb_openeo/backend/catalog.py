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


import datetime

from ..core.vectorcube import VectorCube, Feature
from ..server.context import RequestContext

API_VERSION = '1.1.0'
STAC_VERSION = '0.9.0'

FILE_FORMATS = {
    'output': {
        'GeoPandas Dataframe': {
            'title': 'GeoDataFrame',
            'description': 'A GeoDataFrame is a tabular data '
                           'structure that contains a geometry '
                           'column.',
            'gis_data_types': ['vector'],
            'links': [{
                'href': 'https://geopandas.org/en/stable/docs/'
                        'reference/api/geopandas.GeoDataFrame.html',
                'rel': 'about',
                'title': 'geopandas.GeoDataFrame'
            }],
            'parameters': {}
        }
    },
    'input': {
        'CSV': {
            'title': 'Comma Separated Value (.csv)',
            'description': 'Must be structured in a way understood '
                           'by the Pandas/GeoPandas Python library.',
            'gis_data_types': ['vector'],
            'links': [{
                'href': 'https://gdal.org/drivers/vector/'
                        'csv.html#vector-csv',
                'rel': 'about',
                'title': 'Comma Separated Value (.csv) - GDAL '
                         'documentation'
            }],
            'parameters': {}
        },
        'GeoJSON': {
            'title': 'GeoJSON',
            'description': 'Must be structured in a way understood '
                           'by the Pandas/GeoPandas Python library.',
            'gis_data_types': ['vector'],
            'links': [{
                'href': 'https://gdal.org/drivers/vector/'
                        'geojson.html#vector-geojson',
                'rel': 'about',
                'title': 'GeoJSON - GDAL documentation'
            }],
            'parameters': {}
        },
        'ESRI Shapefile': {
            'title': 'ESRI Shapefile / DBF',
            'description': 'Must be structured in a way understood '
                           'by the Pandas/GeoPandas Python library.',
            'gis_data_types': ['vector'],
            'links': [{
                'href': 'https://gdal.org/drivers/vector/'
                        'shapefile.html#vector-shapefile',
                'rel': 'about',
                'title': 'ESRI Shapefile / DBF - GDAL documentation'
            }],
            'parameters': {}
        }

    }
}


def get_collections(ctx: RequestContext):
    return {
        'collections': [
            _get_vector_cube_collection(ctx,
                                        ctx.get_vector_cube(collection_id),
                                        details=False)
            for collection_id in ctx.collection_ids
        ],
        'links': [
            # todo - if too many collections are listed, implement
            #  pagination. See
            #  https://openeo.org/documentation/1.0/developers/api/reference.html#operation/list-collections
        ]
    }


def get_collection(ctx: RequestContext,
                   collection_id: str):
    vector_cube = _get_vector_cube(ctx, collection_id)
    return _get_vector_cube_collection(ctx,
                                       vector_cube,
                                       details=True)


def get_collection_items(ctx: RequestContext,
                         collection_id: str):
    vector_cube = _get_vector_cube(ctx, collection_id)
    stac_features = [
        _get_vector_cube_item(ctx,
                              vector_cube,
                              feature,
                              details=False)
        for feature in vector_cube.get("features", [])
    ]

    return {
        "type": "FeatureCollection",
        "features": stac_features,
        "timeStamp": _utc_now(),
        "numberMatched": len(stac_features),
        "numberReturned": len(stac_features),
    }


def get_collection_item(ctx: RequestContext,
                        collection_id: str,
                        feature_id: str):
    vector_cube = _get_vector_cube(ctx, collection_id)
    for feature in vector_cube.get("features", []):
        if feature.get("id") == feature_id:
            return _get_vector_cube_item(ctx,
                                         vector_cube,
                                         feature,
                                         details=True)
    raise ItemNotFoundException(
        f'feature {feature_id!r} not found in collection {collection_id!r}'
    )


def search(ctx: RequestContext):
    # TODO: implement me
    return {}


def _get_vector_cube_collection(ctx: RequestContext,
                                vector_cube: VectorCube,
                                details: bool = False):
    config = ctx.config
    vector_cube_id = vector_cube["id"]
    metadata = vector_cube.get("metadata", {})
    return {
        "stac_version": STAC_VERSION,
        "stac_extensions": ["xcube-geodb"],
        "id": vector_cube_id,
        # TODO: fill in values
        "title": metadata.get("title", ""),
        "description": metadata.get("description", ""),
        "license": metadata.get("license", "proprietary"),
        "keywords": metadata.get("keywords", []),
        "providers": metadata.get("providers", []),
        "extent": metadata.get("extent", {}),
        "summaries": metadata.get("summaries", {}),
        "links": [
            {
                "rel": "self",
                "href": ctx.get_url(
                    f"collections/{vector_cube_id}")
            },
            {
                "rel": "root",
                "href": ctx.get_url("collections")
            },
            # {
            #     "rel": "license",
            #     "href": ctx.get_url("TODO"),
            #     "title": "TODO"
            # }
        ]
    }


def _get_vector_cube_item(ctx: RequestContext,
                          vector_cube: VectorCube,
                          feature: Feature,
                          details: bool = False):
    collection_id = vector_cube["id"]
    feature_id = feature["id"]
    feature_bbox = feature.get("bbox")
    feature_geometry = feature.get("geometry")
    feature_properties = feature.get("properties", {})

    return {
        "stac_version": STAC_VERSION,
        "stac_extensions": ["xcube-geodb"],
        "type": "Feature",
        "id": feature_id,
        "bbox": feature_bbox,
        "geometry": feature_geometry,
        "properties": feature_properties,
        "collection": collection_id,
        "links": [
            {
                "rel": "self",
                'href': ctx.get_url(f'catalog/'
                                    f'collections/{collection_id}/'
                                    f'items/{feature_id}')
            }
        ],
        "assets": {
            "analytic": {
                # TODO
            },
            "visual": {
                # TODO
            },
            "thumbnail": {
                # TODO
            }
        }
    }


def _utc_now():
    return datetime \
               .datetime \
               .utcnow() \
               .replace(microsecond=0) \
               .isoformat() + 'Z'


def _get_vector_cube(ctx, collection_id):
    if collection_id not in ctx.collection_ids:
        raise CollectionNotFoundException(
            f'Unknown collection {collection_id!r}'
        )
    return ctx.get_vector_cube(collection_id)


class CollectionNotFoundException(Exception):
    pass


class ItemNotFoundException(Exception):
    pass
