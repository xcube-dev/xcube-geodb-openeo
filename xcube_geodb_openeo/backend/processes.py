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

def get_processors():
    return {
        'processes': [
            {
                'id': 'load_collection',
                'summary': 'Load a collection.',
                'categories': ['import'],
                'description': 'Loads a collection from the current back-end '
                               'by its id and returns it as a vector cube.'
                               'The data that is added to the data cube can be'
                               ' restricted with the parameters'
                               '"spatial_extent" and "properties".',
                'parameters': [
                    {
                        'name': 'id',
                        'description': 'The collection\'s name',
                        'schema': {
                            'type': 'string'
                        }
                    },
                    {
                        'name': 'database',
                        'description': 'The database of the collection',
                        'schema': {
                            'type': 'string'
                        },
                        'optional': True
                    },
                    {
                        "name": "spatial_extent",
                        "description":
                            "Limits the data to load from the collection to"
                            " the specified bounding box or polygons.\n\nThe "
                            "process puts a pixel into the data cube if the "
                            "point at the pixel center intersects with the "
                            "bounding box or any of the polygons (as defined "
                            "in the Simple Features standard by the OGC).\n\n"
                            "The GeoJSON can be one of the following feature "
                            "types:\n\n* A `Polygon` or `MultiPolygon` "
                            "geometry,\n* a `Feature` with a `Polygon` or "
                            "`MultiPolygon` geometry,\n* a "
                            "`FeatureCollection` containing at least one "
                            "`Feature` with `Polygon` or `MultiPolygon` "
                            "geometries, or\n* a `GeometryCollection` "
                            "containing `Polygon` or `MultiPolygon` "
                            "geometries. To maximize interoperability, "
                            "`GeometryCollection` should be avoided in favour "
                            "of one of the alternatives above.\n\nSet this "
                            "parameter to `null` to set no limit for the "
                            "spatial extent. Be careful with this when "
                            "loading large datasets! It is recommended to use "
                            "this parameter instead of using "
                            "``filter_bbox()`` or ``filter_spatial()`` "
                            "directly after loading unbounded data.",
                        "schema": [
                            {
                                "title": "Bounding Box",
                                "type": "object",
                                "subtype": "bounding-box",
                                "required": [
                                    "west",
                                    "south",
                                    "east",
                                    "north"
                                ],
                                "properties": {
                                    "west": {
                                        "description":
                                            "West (lower left corner, "
                                            "coordinate axis 1).",
                                        "type": "number"
                                    },
                                    "south": {
                                        "description":
                                            "South (lower left corner, "
                                            "coordinate axis 2).",
                                        "type": "number"
                                    },
                                    "east": {
                                        "description":
                                            "East (upper right corner, "
                                            "coordinate axis 1).",
                                        "type": "number"
                                    },
                                    "north": {
                                        "description":
                                            "North (upper right corner, "
                                            "coordinate axis 2).",
                                        "type": "number"
                                    },
                                    "base": {
                                        "description":
                                            "Base (optional, lower left "
                                            "corner, coordinate axis 3).",
                                        "type": [
                                            "number",
                                            "null"
                                        ],
                                        "default": "null"
                                    },
                                    "height": {
                                        "description": "Height (optional, upper right corner, coordinate axis 3).",
                                        "type": [
                                            "number",
                                            "null"
                                        ],
                                        "default": "null"
                                    },
                                    "crs": {
                                        "description": "Coordinate reference system of the extent, specified as as [EPSG code](http://www.epsg-registry.org/), [WKT2 (ISO 19162) string](http://docs.opengeospatial.org/is/18-010r7/18-010r7.html) or [PROJ definition (deprecated)](https://proj.org/usage/quickstart.html). Defaults to `4326` (EPSG code 4326) unless the client explicitly requests a different coordinate reference system.",
                                        "anyOf": [
                                            {
                                                "title": "EPSG Code",
                                                "type": "integer",
                                                "subtype": "epsg-code",
                                                "minimum": 1000,
                                                "examples": [
                                                    3857
                                                ]
                                            },
                                            {
                                                "title": "WKT2",
                                                "type": "string",
                                                "subtype": "wkt2-definition"
                                            },
                                            {
                                                "title": "PROJ definition",
                                                "type": "string",
                                                "subtype": "proj-definition",
                                                "deprecated": True
                                            }
                                        ],
                                        "default": 4326
                                    }
                                }
                            },
                            {
                                "title": "GeoJSON",
                                "description":
                                    "Limits the data cube to the bounding box "
                                    "of the given geometry. All pixels inside "
                                    "the bounding box that do not intersect "
                                    "with any of the polygons will be set to "
                                    "no data (`null`).",
                                "type": "object",
                                "subtype": "geojson"
                            },
                            {
                                "title": "No filter",
                                "description":
                                    "Don't filter spatially. All data is "
                                    "included in the data cube.",
                                "type": "null"
                            }
                        ]
                    }
                ],
                'returns': {
                    'description': 'A vector cube for further processing.',
                    'schema': {
                        "type": "object",
                        "subtype": "vector-cube"
                    }
                }
            }
        ],
        'links': []
    }
