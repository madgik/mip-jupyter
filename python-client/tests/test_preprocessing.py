import unittest

from mip.preprocessing import MissingValuesHandler
from mip.preprocessing import OutlierWinsorizer


class Var:
    def __init__(self, code):
        self.code = code


class TestPreprocessing(unittest.TestCase):
    def test_missing_values_handler_serializes_variable_keys(self):
        age = Var("age")
        apoe4 = Var("apoe4")
        spec = MissingValuesHandler(
            strategies={age: "median", apoe4: "constant"},
            fill_values={apoe4: "unknown"},
        ).spec()

        self.assertEqual(spec["name"], "missing_values_handler")
        self.assertEqual(spec["parameters"]["strategies"], {"age": "median", "apoe4": "constant"})
        self.assertEqual(spec["parameters"]["fill_values"], {"apoe4": "unknown"})

    def test_outlier_winsorizer_omits_empty_optional_maps(self):
        mmse = Var("mmse")
        spec = OutlierWinsorizer(strategies={mmse: "iqr"}, tails={mmse: "both"}, folds={mmse: 1.5}).spec()

        self.assertEqual(spec["name"], "outlier_winsorizer")
        self.assertEqual(spec["parameters"]["strategies"], {"mmse": "iqr"})
        self.assertEqual(spec["parameters"]["tails"], {"mmse": "both"})
        self.assertEqual(spec["parameters"]["folds"], {"mmse": 1.5})
        self.assertNotIn("fill_values", spec["parameters"])


if __name__ == "__main__":
    unittest.main()
