import unittest

from mip.preprocessing import LongitudinalTransformer
from mip.preprocessing import MissingValuesHandler
from mip.preprocessing import OutlierWinsorizer


class Var:
    def __init__(self, code, *, label=None):
        self._code = code
        self.label = label or code


class TestPreprocessing(unittest.TestCase):
    def test_missing_values_handler_serializes_variable_keys(self):
        age = Var("age", label="Age")
        apoe4 = Var("apoe4", label="APOE4")
        handler = MissingValuesHandler(
            strategies={age: "median", apoe4: "constant"},
            fill_values={apoe4: "unknown"},
        )
        spec = handler.spec()

        self.assertEqual(spec["name"], "missing_values_handler")
        self.assertEqual(spec["parameters"]["strategies"], {"age": "median", "apoe4": "constant"})
        self.assertEqual(spec["parameters"]["fill_values"], {"apoe4": "unknown"})
        self.assertEqual(
            handler.user_summary()["strategies"],
            {"Age": "median", "APOE4": "constant"},
        )

    def test_outlier_winsorizer_omits_empty_optional_maps(self):
        mmse = Var("mmse", label="MMSE")
        handler = OutlierWinsorizer(strategies={mmse: "iqr"}, tails={mmse: "both"}, folds={mmse: 1.5})
        spec = handler.spec()

        self.assertEqual(spec["name"], "outlier_winsorizer")
        self.assertEqual(spec["parameters"]["strategies"], {"mmse": "iqr"})
        self.assertEqual(spec["parameters"]["tails"], {"mmse": "both"})
        self.assertEqual(spec["parameters"]["folds"], {"mmse": 1.5})
        self.assertNotIn("fill_values", spec["parameters"])
        self.assertEqual(handler.user_summary()["strategies"], {"MMSE": "iqr"})

    def test_longitudinal_transformer_serializes_visit_and_strategies(self):
        age = Var("age", label="Age")
        mmse = Var("mmse", label="MMSE")
        transformer = LongitudinalTransformer(
            visit1="BL",
            visit2="FL1",
            strategies={age: "diff", mmse: "second"},
        )
        spec = transformer.spec()

        self.assertEqual(spec["name"], "longitudinal_transformer")
        self.assertEqual(spec["parameters"]["visit1"], "BL")
        self.assertEqual(spec["parameters"]["visit2"], "FL1")
        self.assertEqual(spec["parameters"]["strategies"], {"age": "diff", "mmse": "second"})
        self.assertEqual(
            transformer.user_summary()["strategies"],
            {"Age": "diff", "MMSE": "second"},
        )


if __name__ == "__main__":
    unittest.main()
