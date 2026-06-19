import unittest
from unittest.mock import MagicMock

from mip.catalog import Catalog


MOCK_DATA_MODELS = [
    {
        "code": "dementia",
        "version": "0.1",
        "label": "Dementia",
        "longitudinal": False,
        "variables": [{"code": "dataset", "label": "Dataset", "type": "nominal"}],
        "groups": [
            {
                "code": "clinical",
                "label": "Clinical",
                "variables": [
                    {"code": "age", "label": "Age", "type": "real"},
                    {"code": "sex", "label": "Sex", "type": "nominal", "enumerations": {"M": "Male", "F": "Female"}},
                ],
                "groups": [
                    {"code": "cognitive", "label": "Cognitive", "variables": [{"code": "mmse", "label": "MMSE", "type": "integer"}]}
                ],
            }
        ],
        "datasets": [{"code": "adni", "label": "ADNI"}],
        "datasetsVariables": {"adni": ["age", "sex", "mmse"]},
    }
]


class TestCatalog(unittest.TestCase):
    def test_data_model_builds_collections(self):
        transport = MagicMock()
        transport.get.return_value = MOCK_DATA_MODELS

        dm = Catalog(transport).data_model("dementia")

        self.assertEqual(dm.name, "dementia:0.1")
        self.assertEqual(dm.variables["age"].label, "Age")
        self.assertEqual(dm.variables["mmse"].code, "mmse")
        self.assertTrue(dm.variables["age"].is_numerical())
        self.assertTrue(dm.variables["sex"].is_categorical())
        self.assertEqual(dm.variables["sex"].categories(), ["M", "F"])
        self.assertEqual(dm.datasets["adni"].variables()[0].code, "age")
        self.assertTrue(dm.datasets["adni"].has_variable(dm.variables["mmse"]))

    def test_search_methods_return_native_lists(self):
        transport = MagicMock()
        transport.get.return_value = MOCK_DATA_MODELS
        catalog = Catalog(transport)

        self.assertIsInstance(catalog.list(), list)
        self.assertEqual(catalog.list()[0].code, "dementia")
        self.assertIsInstance(catalog.summaries(), list)
        self.assertEqual(catalog.summaries()[0]["code"], "dementia")
        self.assertIn("Data models", str(catalog.tree()))
        self.assertIsInstance(catalog.search_variables("MMSE"), list)
        self.assertEqual(catalog.search_variables("MMSE")[0].code, "mmse")
        self.assertIsInstance(catalog.search_datasets("adni"), list)
        self.assertEqual(catalog.search_datasets("adni")[0].code, "adni")
        dm = catalog.data_model("dementia")
        self.assertIsInstance(dm.variables.search("MMSE"), list)
        self.assertEqual(dm.variables.search("MMSE")[0].code, "mmse")

    def test_data_model_list_and_tree_helpers(self):
        transport = MagicMock()
        transport.get.return_value = MOCK_DATA_MODELS
        dm = Catalog(transport).data_model("dementia")

        self.assertEqual(dm.list_datasets()[0]["code"], "adni")
        self.assertEqual(dm.datasets.list()[0].code, "adni")
        self.assertEqual(dm.list_variables()[0]["code"], "dataset")
        self.assertIn("groups", str(dm.tree()))
        self.assertIn("MMSE", str(dm.tree(include_variables=True)))
        self.assertIn("MMSE", str(dm.variables.tree()))
        self.assertIn("Clinical", str(dm.tree(group="clinical", include_variables=True)))
        self.assertIn("MMSE", str(dm.tree(group="cognitive", include_variables=True)))
        self.assertIn("MMSE", str(dm.variables.tree(group="cognitive")))
        self.assertEqual(
            [item["code"] for item in dm.list_groups()],
            ["clinical", "cognitive"],
        )

    def test_unknown_group_raises_lookup_error(self):
        transport = MagicMock()
        transport.get.return_value = MOCK_DATA_MODELS
        dm = Catalog(transport).data_model("dementia")
        with self.assertRaises(LookupError):
            dm.tree(group="missing")

    def test_ambiguous_data_model_requires_version(self):
        transport = MagicMock()
        transport.get.return_value = [*MOCK_DATA_MODELS, {**MOCK_DATA_MODELS[0], "version": "0.2"}]
        with self.assertRaises(LookupError):
            Catalog(transport).data_model("dementia")


if __name__ == "__main__":
    unittest.main()
