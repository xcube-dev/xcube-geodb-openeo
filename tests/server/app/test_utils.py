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

from xcube_geodb_openeo.defaults import STAC_EXTENSIONS


def assert_paderborn(cls, vector_cube):
    cls.assertIsNotNone(vector_cube)
    cls.assertEqual('1.0.0', vector_cube['stac_version'])
    cls.assertEqual(STAC_EXTENSIONS, vector_cube['stac_extensions'])
    cls.assertEqual('Feature', vector_cube['type'])
    cls.assertEqual('1', vector_cube['id'])
    assert_paderborn_data(cls, vector_cube)


def assert_paderborn_data(cls, vector_cube):
    cls.assertEqual(['8.7000', '51.3000', '8.8000', '51.8000'],
                    vector_cube['bbox'])
    cls.assertEqual({'type': 'Polygon', 'coordinates': [[[8.7, 51.3],
                                                         [8.7, 51.8],
                                                         [8.8, 51.8],
                                                         [8.8, 51.3],
                                                         [8.7, 51.3]
                                                         ]]},
                    vector_cube['geometry'])
    cls.assertEqual({'name': 'paderborn', 'population': 150000},
                    vector_cube['properties'])


def assert_hamburg(cls, vector_cube):
    cls.assertEqual('1.0.0', vector_cube['stac_version'])
    cls.assertEqual(STAC_EXTENSIONS, vector_cube['stac_extensions'])
    cls.assertEqual('Feature', vector_cube['type'])
    cls.assertEqual('0', vector_cube['id'])
    assert_hamburg_data(cls, vector_cube)


def assert_hamburg_data(cls, vector_cube):
    cls.assertEqual(['9.0000', '52.0000', '11.0000', '54.0000'],
                    vector_cube['bbox'])
    cls.assertEqual({'type': 'Polygon', 'coordinates': [[[9, 52],
                                                         [9, 54],
                                                         [11, 54],
                                                         [11, 52],
                                                         [10, 53],
                                                         [9.8, 53.4],
                                                         [9.2, 52.1],
                                                         [9, 52]]]},
                    vector_cube['geometry'])
    cls.assertEqual({'name': 'hamburg', 'population': 1700000},
                    vector_cube['properties'])
