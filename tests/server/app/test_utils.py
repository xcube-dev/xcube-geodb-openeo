def assert_paderborn(cls, item_data):
    cls.assertIsNotNone(item_data)
    cls.assertEqual('0.9.0', item_data['stac_version'])
    cls.assertEqual(['xcube-geodb'], item_data['stac_extensions'])
    cls.assertEqual('Feature', item_data['type'])
    cls.assertEqual('1', item_data['id'])
    cls.assertEqual(['8.7000', '51.3000', '8.8000', '51.8000'],
                    item_data['bbox'])
    cls.assertEqual({'type': 'Polygon', 'coordinates': [[[8.7, 51.3],
                                                         [8.7, 51.8],
                                                         [8.8, 51.8],
                                                         [8.8, 51.3],
                                                         [8.7, 51.3]
                                                         ]]},
                    item_data['geometry'])
    cls.assertEqual({'name': 'paderborn', 'population': 150000},
                    item_data['properties'])


def assert_hamburg(cls, item_data):
    cls.assertEqual('0.9.0', item_data['stac_version'])
    cls.assertEqual(['xcube-geodb'], item_data['stac_extensions'])
    cls.assertEqual('Feature', item_data['type'])
    cls.assertEqual('0', item_data['id'])
    cls.assertEqual(['9.0000', '52.0000', '11.0000', '54.0000'],
                    item_data['bbox'])
    cls.assertEqual({'type': 'Polygon', 'coordinates': [[[9, 52],
                                                         [9, 54],
                                                         [11, 54],
                                                         [11, 52],
                                                         [10, 53],
                                                         [9.8, 53.4],
                                                         [9.2, 52.1],
                                                         [9, 52]]]},
                    item_data['geometry'])
    cls.assertEqual({'name': 'hamburg', 'population': 1700000},
                    item_data['properties'])