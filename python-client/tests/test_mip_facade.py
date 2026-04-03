import unittest
from unittest.mock import patch

from mip import (
    FederatedLinearRegression,
    FederatedLogisticRegression,
    FederatedNaiveBayes,
    configure as backend_configure,
)

from mip import algorithms
from mip import configure
from mip import experiments
from mip import filters
from mip import metadata


class TestMipFacadeImports(unittest.TestCase):
    def test_configure_is_reexported(self):
        self.assertIs(configure, backend_configure)

    def test_model_wrappers_are_reexported(self):
        from mip import FederatedLinearRegression as mip_lr
        from mip import FederatedLogisticRegression as mip_logr
        from mip import FederatedNaiveBayes as mip_nb

        self.assertIs(mip_logr, FederatedLogisticRegression)
        self.assertIs(mip_lr, FederatedLinearRegression)
        self.assertIs(mip_nb, FederatedNaiveBayes)


class TestMetadataModule(unittest.TestCase):
    @patch("mip.metadata.DataModel.list")
    def test_get_pathology_by_code_version(self, mock_list):
        mock_list.return_value = [
            metadata.DataModel(
                {
                    "code": "dementia",
                    "version": "0.1",
                    "label": "Dementia",
                    "variables": [{"code": "age"}],
                    "datasets": ["edsd"],
                }
            )
        ]

        pathology = metadata.get_pathology("dementia:0.1")
        self.assertEqual(pathology.name, "dementia:0.1")
        self.assertEqual(pathology.variables, [{"code": "age"}])
        self.assertEqual(pathology.datasets, ["edsd"])

    @patch("mip.metadata.DataModel.list")
    def test_get_pathology_by_code_requires_explicit_version_when_ambiguous(self, mock_list):
        mock_list.return_value = [
            metadata.DataModel({"code": "dementia", "version": "0.1"}),
            metadata.DataModel({"code": "dementia", "version": "0.2"}),
        ]
        with self.assertRaises(LookupError):
            metadata.get_pathology("dementia")

    @patch("mip.metadata.DataModel.list")
    def test_describe_single_pathology_tree(self, mock_list):
        mock_list.return_value = [
            metadata.DataModel(
                {
                    "code": "dementia",
                    "version": "0.1",
                    "label": "Dementia",
                    "datasets": [{"code": "edsd", "label": "EDSD"}],
                    "variables": [{"code": "dataset", "label": "Dataset", "type": "nominal", "sql_type": "text"}],
                    "groups": [
                        {
                            "code": "brain",
                            "label": "Brain",
                            "variables": [{"code": "age", "label": "Age", "type": "real", "sql_type": "real"}],
                            "groups": [
                                {
                                    "code": "sub",
                                    "label": "Sub",
                                    "variables": [{"code": "mmse", "label": "MMSE", "type": "integer", "sql_type": "integer"}],
                                }
                            ],
                        }
                    ],
                    "datasetsVariables": {"edsd": ["dataset", "age", "mmse"]},
                }
            )
        ]

        text = metadata.describe("dementia:0.1", include_variables=True, max_lines=200)
        self.assertIsInstance(text, str)
        self.assertIn("Metadata tree for dementia:0.1 (Dementia)", text)
        self.assertIn("datasets (1)", text)
        self.assertIn("EDSD", text)
        self.assertNotIn("`-- edsd", text)
        self.assertIn("groups (1)", text)
        self.assertIn("Brain [1 vars, 1 groups]", text)
        self.assertIn("Age [real]", text)
        self.assertNotIn("datasets_variables", text)

    @patch("mip.metadata.DataModel.list")
    def test_describe_catalog_summary(self, mock_list):
        mock_list.return_value = [
            metadata.DataModel(
                {
                    "code": "dementia",
                    "version": "0.1",
                    "datasets": [{"code": "edsd", "label": "EDSD"}],
                    "variables": [{"code": "dataset"}],
                    "groups": [{"code": "brain", "variables": [{"code": "age"}]}],
                }
            ),
            metadata.DataModel(
                {
                    "code": "tbi",
                    "version": "0.1",
                    "datasets": [{"code": "dummy", "label": "Dummy"}],
                    "variables": [{"code": "dataset"}],
                    "groups": [],
                }
            ),
        ]

        text = metadata.describe()
        self.assertIn("Data models (2)", text)
        self.assertIn("dementia:0.1", text)
        self.assertIn("tbi:0.1", text)

class TestAlgorithmsModule(unittest.TestCase):
    @patch("mip.algorithms.Algorithm.list")
    def test_list_delegates_to_backend_client(self, mock_list):
        sentinel = object()
        mock_list.return_value = [sentinel]
        result = algorithms.list()
        self.assertEqual(result, [sentinel])


class TestExperimentsModule(unittest.TestCase):
    @patch("mip.experiments.Experiment.create")
    def test_create_delegates_to_backend_client(self, mock_create):
        sentinel = object()
        mock_create.return_value = sentinel
        result = experiments.create(
            name="exp",
            algorithm_name="linear_regression",
            data_model="dementia:0.1",
            datasets=["edsd"],
            x=["age"],
            y=["target"],
        )
        self.assertIs(result, sentinel)
        _, kwargs = mock_create.call_args
        self.assertEqual(kwargs["algorithm_name"], "linear_regression")
        self.assertEqual(kwargs["data_model"], "dementia:0.1")

    @patch("mip.experiments.Experiment.run_transient")
    def test_run_transient_delegates_to_backend_client(self, mock_run_transient):
        sentinel = object()
        mock_run_transient.return_value = sentinel
        result = experiments.run_transient(
            name="exp",
            algorithm_name="descriptive_stats",
            data_model="dementia:0.1",
            datasets=["edsd"],
            x=["age"],
            y=["target"],
        )
        self.assertIs(result, sentinel)
        _, kwargs = mock_run_transient.call_args
        self.assertEqual(kwargs["algorithm_name"], "descriptive_stats")


class TestFiltersModule(unittest.TestCase):
    def test_ruleset_accepts_tuple_rules(self):
        ruleset = filters.RULESET(
            [
                ("age", filters.GREATER, 60),
                ("gender", filters.EQUAL, "M"),
            ],
            filters.AND,
        )
        self.assertEqual(ruleset["condition"], "AND")
        self.assertEqual(len(ruleset["rules"]), 2)
        self.assertEqual(ruleset["rules"][0]["id"], "age")
        self.assertEqual(ruleset["rules"][0]["operator"], "greater")
        self.assertEqual(ruleset["rules"][0]["type"], "integer")
        self.assertEqual(ruleset["rules"][1]["type"], "string")


if __name__ == "__main__":
    unittest.main()
