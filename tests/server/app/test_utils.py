def assert_paderborn(cls, vector_cube):
    cls.assertIsNotNone(vector_cube)
    cls.assertEqual('1.0.0', vector_cube['stac_version'])
    cls.assertEqual(
        ['datacube',
         'https://stac-extensions.github.io/version/v1.0.0/schema.json'],
        vector_cube['stac_extensions'])
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
    cls.assertEqual(
        ['datacube',
         'https://stac-extensions.github.io/version/v1.0.0/schema.json'],
        vector_cube['stac_extensions'])
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
