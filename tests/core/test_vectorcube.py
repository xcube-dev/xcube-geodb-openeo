import unittest

from tests.core.mock_vc_provider import MockProvider


class VectorCubeTest(unittest.TestCase):

    def test_to_geojson(self):
        mp = MockProvider({})
        vc = mp.get_vector_cube(('', 'collection_1'))
        gj = vc.to_geojson()
        self.assertEqual(2, len(gj['features']))
        self.assertEqual('FeatureCollection', gj['type'])

        feature_1 = gj['features'][0]
        feature_2 = gj['features'][1]

        self.assertEqual([
            "9.0000",
            "52.0000",
            "11.0000",
            "54.0000"
        ], feature_1['bbox'])
        self.assertEqual([
            "8.7000",
            "51.3000",
            "8.8000",
            "51.8000"
        ], feature_2['bbox'])
        self.assertEqual([
            "datacube",
            "https://stac-extensions.github.io/version/v1.0.0/schema.json"
        ], feature_1['stac_extensions'])
        self.assertEqual([
            "datacube",
            "https://stac-extensions.github.io/version/v1.0.0/schema.json"
        ], feature_2['stac_extensions'])
