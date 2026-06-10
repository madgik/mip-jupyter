import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from mip import MetadataTree
from mip import catalog
from mip import configure


MOCK_DATA_MODELS = [
    {
        "code": "dementia",
        "version": "0.1",
        "label": "Dementia",
        "longitudinal": False,
        "variables": [{"code": "dataset", "label": "Dataset", "type": "nominal"}],
        "groups": [
            {
                "code": "brain",
                "label": "Brain",
                "variables": [{"code": "age", "label": "Age", "type": "real"}],
                "groups": [],
            }
        ],
        "datasets": [{"code": "edsd", "label": "EDSD"}],
        "datasetsVariables": {"edsd": ["dataset", "age"]},
    },
    {
        "code": "dementia",
        "version": "0.2",
        "label": "Dementia v2",
        "longitudinal": True,
        "variables": [],
        "groups": [],
        "datasets": [{"code": "edsd2", "label": "EDSD 2"}],
        "datasetsVariables": {},
    },
]


class TestCatalog(unittest.TestCase):
    def setUp(self):
        configure(base_url="http://mock-backend", token="mock-token")

    @patch("mip.data_model.get_client")
    def test_models_returns_dataframe_columns(self, mock_get_client):
        client = MagicMock()
        client.get.return_value = MOCK_DATA_MODELS
        mock_get_client.return_value = client

        frame = catalog.models(client=client).to_dataframe()
        self.assertEqual(len(frame), 2)
        self.assertIn("name", frame.columns)
        self.assertEqual(frame.loc[0, "name"], "dementia:0.1")
        self.assertEqual(frame.loc[0, "n_datasets"], 1)
        client.get.assert_called_with("/data-models")

    @patch("mip.data_model.get_client")
    def test_datasets_returns_rows_for_model(self, mock_get_client):
        client = MagicMock()
        client.get.return_value = MOCK_DATA_MODELS
        mock_get_client.return_value = client

        frame = catalog.datasets("dementia:0.1", client=client).to_dataframe()
        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.loc[0, "code"], "edsd")
        self.assertEqual(frame.loc[0, "label"], "EDSD")
        self.assertEqual(frame.loc[0, "data_model"], "dementia:0.1")

    @patch("mip.data_model.get_client")
    def test_get_resolves_unambiguous_code(self, mock_get_client):
        client = MagicMock()
        client.get.return_value = [MOCK_DATA_MODELS[0]]
        mock_get_client.return_value = client

        model = catalog.get("dementia", client=client)
        self.assertEqual(model.name, "dementia:0.1")

    @patch("mip.data_model.get_client")
    def test_get_raises_for_ambiguous_code(self, mock_get_client):
        client = MagicMock()
        client.get.return_value = MOCK_DATA_MODELS
        mock_get_client.return_value = client

        with self.assertRaises(LookupError):
            catalog.get("dementia", client=client)

    @patch("mip.data_model.get_client")
    def test_visualize_renders_tree_with_groups_and_datasets(self, mock_get_client):
        client = MagicMock()
        client.get.return_value = [MOCK_DATA_MODELS[0]]
        mock_get_client.return_value = client

        tree = catalog.visualize("dementia:0.1", include_variables=True, client=client)
        self.assertIsInstance(tree, MetadataTree)
        text = str(tree)
        self.assertIn("Metadata tree for dementia:0.1", text)
        self.assertIn("EDSD", text)
        self.assertIn("Brain", text)
        self.assertIn("Age [real]", text)

    @patch("mip.data_model.get_client")
    def test_visualize_all_renders_catalog_summary(self, mock_get_client):
        client = MagicMock()
        client.get.return_value = MOCK_DATA_MODELS
        mock_get_client.return_value = client

        tree = catalog.visualize_all(client=client)
        self.assertIn("Data models (2)", str(tree))
        self.assertIn("Dementia:0.1", str(tree))

    def test_metadata_tree_display_fallback(self):
        tree = MetadataTree("line one\nline two")
        tree.display()


if __name__ == "__main__":
    unittest.main()
