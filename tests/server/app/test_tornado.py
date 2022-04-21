import re
import unittest

from xcube_geodb_openeo.server.app.tornado import App


class UrlPatternTest(unittest.TestCase):
    def test_url_pattern_works(self):
        re_pattern = App.url_pattern('/open/{id1}ws/{id2}wf')
        matcher = re.fullmatch(re_pattern, '/open/34ws/a66wf')
        self.assertIsNotNone(matcher)
        self.assertEqual(matcher.groupdict(), {'id1': '34', 'id2': 'a66'})

        re_pattern = App.url_pattern('/open/ws{id1}/wf{id2}')
        matcher = re.fullmatch(re_pattern, '/open/ws34/wfa66')
        self.assertIsNotNone(matcher)
        self.assertEqual(matcher.groupdict(), {'id1': '34', 'id2': 'a66'})

        re_pattern = App.url_pattern(
            '/datasets/{ds_id}/data.zarr/(?P<path>.*)'
        )

        matcher = re.fullmatch(re_pattern,
                               '/datasets/S2PLUS_2017/data.zarr/')
        self.assertIsNotNone(matcher)
        self.assertEqual(matcher.groupdict(),
                         {'ds_id': 'S2PLUS_2017', 'path': ''})

        matcher = re.fullmatch(re_pattern,
                               '/datasets/S2PLUS_2017/'
                               'data.zarr/conc_chl/.zattrs')
        self.assertIsNotNone(matcher)
        self.assertEqual(matcher.groupdict(),
                         {'ds_id': 'S2PLUS_2017', 'path': 'conc_chl/.zattrs'})

        x = 'C%3A%5CUsers%5CNorman%5C' \
            'IdeaProjects%5Cccitools%5Cect-core%5Ctest%5Cui%5CTEST_WS_3'
        re_pattern = App.url_pattern('/ws/{base_dir}/res/{res_name}/add')
        matcher = re.fullmatch(re_pattern, '/ws/%s/res/SST/add' % x)
        self.assertIsNotNone(matcher)
        self.assertEqual(matcher.groupdict(),
                         {'base_dir': x, 'res_name': 'SST'})

    def test_url_pattern_ok(self):
        self.assertEqual('/version',
                         App.url_pattern('/version'))
        self.assertEqual(r'(?P<num>[^\;\/\?\:\@\&\=\+\$\,]+)/get',
                         App.url_pattern('{num}/get'))
        self.assertEqual(r'/open/(?P<ws_name>[^\;\/\?\:\@\&\=\+\$\,]+)',
                         App.url_pattern('/open/{ws_name}'))
        self.assertEqual(
            r'/open/ws(?P<id1>[^\;\/\?\:\@\&\=\+\$\,]+)/'
            r'wf(?P<id2>[^\;\/\?\:\@\&\=\+\$\,]+)',
            App.url_pattern('/open/ws{id1}/wf{id2}'))
        self.assertEqual(
            r'/datasets/(?P<ds_id>[^\;\/\?\:\@\&\=\+\$\,]+)/data.zip/(.*)',
            App.url_pattern('/datasets/{ds_id}/data.zip/(.*)'))

    def test_url_pattern_fail(self):
        with self.assertRaises(ValueError) as cm:
            App.url_pattern('/open/{ws/name}')
        self.assertEqual('NAME in "{NAME}" must be a valid identifier,'
                         ' but got "ws/name"',
                         str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            App.url_pattern('/info/{id')
        self.assertEqual('closing "}" missing after opening "{"',
                         str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            App.url_pattern('/info/id}')
        self.assertEqual('closing "}" without opening "{"',
                         str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            App.url_pattern('/info/{id}/{x}}')
        self.assertEqual('closing "}" without opening "{"',
                         str(cm.exception))
