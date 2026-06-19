import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from mip import AnalysisSet
from mip import Pipeline
from mip.filters import F
from mip.preprocessing import CategoricalColumnCreator
from mip.preprocessing import MissingValuesHandler
from mip.preprocessing import OutlierWinsorizer


class Var:
    def __init__(self, code):
        self.code = code


class TestPipeline(unittest.TestCase):
    def test_histogram_posts_transient_payload(self):
        transport = MagicMock()
        transport.post.return_value = {"status": "success", "result": {"bins": [1, 2], "counts": [3, 4]}}
        dm = SimpleNamespace(code="dementia", version="0.1", _transport=transport)
        adni = SimpleNamespace(code="adni")
        age = Var("age")
        mmse = Var("mmse")
        analysis_set = AnalysisSet(data_model=dm, datasets=[adni], variables=[age, mmse])

        result = Pipeline(
            analysis_set=analysis_set,
            filters=F(age) >= 50,
            handle_missing=MissingValuesHandler(strategies={mmse: "mean"}),
            outlier_handling=OutlierWinsorizer(strategies={mmse: "iqr"}),
        ).histogram(variable=mmse, bins=20)

        endpoint, payload = transport.post.call_args.args
        analysis = payload["analysis"]
        self.assertEqual(endpoint, "/experiments/transient")
        self.assertEqual(analysis["algorithm"]["name"], "histogram")
        self.assertEqual(analysis["algorithm"]["y"], ["mmse"])
        self.assertEqual(analysis["algorithm"]["parameters"], {"bins": 20})
        self.assertEqual(analysis["inputdata"]["validation_datasets"], None)
        self.assertIn("age", analysis["inputdata"]["variables"])
        self.assertIn("mmse", analysis["inputdata"]["variables"])
        self.assertEqual(
            [step["name"] for step in analysis["preprocessing"]],
            ["missing_values_handler", "outlier_winsorizer"],
        )
        self.assertNotIn("mipVersion", payload)
        self.assertEqual(result.raw, {"bins": [1, 2], "counts": [3, 4]})

    def test_logistic_regression_uses_persisted_endpoint(self):
        transport = MagicMock()
        transport.post.return_value = {"status": "success", "result": {"summary": {"feature_names": ["Intercept", "age"], "coefficients": [0.1, 0.5]}}}
        dm = SimpleNamespace(code="dementia", version="0.1", _transport=transport)
        age = Var("age")
        diagnosis = Var("diagnosis")
        analysis_set = AnalysisSet(data_model=dm, datasets=[SimpleNamespace(code="adni")], variables=[age, diagnosis])

        result = Pipeline(analysis_set=analysis_set).logistic_regression(x=[age], y=diagnosis, positive_class="AD", mode="persisted")

        endpoint, payload = transport.post.call_args.args
        analysis = payload["analysis"]
        self.assertEqual(endpoint, "/experiments")
        self.assertEqual(analysis["algorithm"]["name"], "logistic_regression")
        self.assertEqual(analysis["algorithm"]["x"], ["age"])
        self.assertEqual(analysis["algorithm"]["y"], ["diagnosis"])
        self.assertEqual(result.result_type, "logistic_regression")

    def test_t_test_serializes_required_backend_parameters(self):
        transport = MagicMock()
        transport.post.return_value = {"status": "success", "result": {}}
        dm = SimpleNamespace(code="dementia", version="0.1", _transport=transport)
        age = Var("age")
        diagnosis = Var("diagnosis")
        analysis_set = AnalysisSet(
            data_model=dm,
            datasets=[SimpleNamespace(code="adni")],
            variables=[age, diagnosis],
        )

        Pipeline(analysis_set=analysis_set).t_test(
            variable=age,
            group_by=diagnosis,
            group_a="AD",
            group_b="CN",
        )

        parameters = transport.post.call_args.args[1]["analysis"]["algorithm"]["parameters"]
        self.assertEqual(
            parameters,
            {
                "alt_hypothesis": "two-sided",
                "alpha": 0.05,
                "groupA": "AD",
                "groupB": "CN",
            },
        )

    def test_pipeline_serializes_new_columns(self):
        transport = MagicMock()
        transport.post.return_value = {"status": "success", "result": {}}
        dm = SimpleNamespace(code="dementia", version="0.1", _transport=transport)
        mmse = Var("mmse")
        cdr = Var("cdr")
        analysis_set = AnalysisSet(
            data_model=dm,
            datasets=[SimpleNamespace(code="adni")],
            variables=[mmse, cdr],
        )
        creator = CategoricalColumnCreator(
            code="cognitive_profile",
            rules={
                "preserved": F(mmse) >= 27,
                "severe": F(mmse) < 20,
            },
            default_enumeration="unclassified",
        )

        Pipeline(
            analysis_set=analysis_set,
            handle_missing=MissingValuesHandler(strategies={mmse: "drop", cdr: "drop"}),
            new_columns=[creator],
        ).histogram(variable=mmse)

        analysis = transport.post.call_args.args[1]["analysis"]
        self.assertEqual(
            [step["name"] for step in analysis["preprocessing"]],
            ["missing_values_handler", "categorical_column_creator"],
        )
        creator_step = analysis["preprocessing"][1]
        self.assertEqual(creator_step["parameters"]["strategy"], "filter_rules")
        self.assertEqual(creator_step["parameters"]["code"], "cognitive_profile")
        self.assertIn("preserved", creator_step["parameters"]["rules"])

    def test_pipeline_logistic_regression_can_use_derived_variable(self):
        transport = MagicMock()
        transport.post.return_value = {"status": "success", "result": {"summary": {}}}
        dm = SimpleNamespace(code="dementia", version="0.1", _transport=transport)
        age = Var("age")
        diagnosis = Var("diagnosis")
        mmse = Var("mmse")
        analysis_set = AnalysisSet(
            data_model=dm,
            datasets=[SimpleNamespace(code="adni")],
            variables=[age, diagnosis, mmse],
        )
        creator = CategoricalColumnCreator(
            code="cognitive_profile",
            rules={"preserved": F(mmse) >= 27},
        )

        Pipeline(
            analysis_set=analysis_set,
            new_columns=[creator],
        ).logistic_regression(x=[age, creator.variable], y=diagnosis, positive_class="AD")

        analysis = transport.post.call_args.args[1]["analysis"]
        self.assertEqual(analysis["algorithm"]["x"], ["age", "cognitive_profile"])
        self.assertNotIn("cognitive_profile", analysis["inputdata"]["variables"])
        self.assertIn("age", analysis["inputdata"]["variables"])
        self.assertIn("mmse", analysis["inputdata"]["variables"])


if __name__ == "__main__":
    unittest.main()
