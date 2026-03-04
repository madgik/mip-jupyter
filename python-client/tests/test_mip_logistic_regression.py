import json
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import numpy as np

from platform_backend_client import FederatedLogisticRegression


class _ExperimentResponse:
    def __init__(self, result):
        self.uuid = "exp-123"
        self.status = "success"
        self.results = result


class _FakeLogisticRegression:
    def predict_proba(self, x):
        x = np.asarray(x, dtype=float)
        logits = x @ self.coef_.T + self.intercept_
        probs = 1.0 / (1.0 + np.exp(-logits))
        probs = probs.reshape(-1, 1)
        return np.hstack([1.0 - probs, probs])

    def predict(self, x):
        probs = self.predict_proba(x)[:, 1]
        return (probs >= 0.5).astype(int)

    def decision_function(self, x):
        x = np.asarray(x, dtype=float)
        return (x @ self.coef_.T + self.intercept_).reshape(-1)


class TestFederatedLogisticRegression(unittest.TestCase):
    def setUp(self):
        self.valid_payload = {
            "name": "Notebook logistic regression",
            "data_model": "dementia:0.1",
            "datasets": ["edsd"],
            "x": ["age_value", "education_level"],
            "y": ["gender"],
            "parameters": {"positive_class": "M"},
        }
        patcher = patch(
            "platform_backend_client.mip_logistic_regression.FederatedLogisticRegression._import_numpy_and_sklearn",
            return_value=(np, _FakeLogisticRegression),
        )
        self._import_patcher = patcher
        self._import_patcher.start()
        self.addCleanup(self._import_patcher.stop)

    @patch("platform_backend_client.mip_logistic_regression.Experiment.run_transient")
    def test_run_from_flat_payload_returns_model(self, mock_run_transient):
        result = {
            "dependent_var": "gender",
            "indep_vars": ["Intercept", "age_value", "education_level"],
            "summary": {
                "coefficients": [0.25, 1.5, -0.4],
            },
        }
        mock_run_transient.return_value = _ExperimentResponse(result=result)

        runner = FederatedLogisticRegression(self.valid_payload, auto_run=False)
        model = runner.run()

        self.assertEqual(runner.experiment_uuid, "exp-123")
        self.assertEqual(model.n_features_in_, 2)
        np.testing.assert_allclose(model.intercept_, np.asarray([0.25]))
        np.testing.assert_allclose(model.coef_, np.asarray([[1.5, -0.4]]))
        self.assertTrue(hasattr(model, "predict"))
        self.assertTrue(hasattr(model, "predict_proba"))

        _, kwargs = mock_run_transient.call_args
        self.assertEqual(kwargs["algorithm_name"], "logistic_regression")
        self.assertEqual(kwargs["name"], self.valid_payload["name"])
        self.assertEqual(kwargs["data_model"], self.valid_payload["data_model"])
        self.assertEqual(kwargs["datasets"], self.valid_payload["datasets"])
        self.assertEqual(kwargs["x"], self.valid_payload["x"])
        self.assertEqual(kwargs["y"], self.valid_payload["y"])
        self.assertEqual(kwargs["parameters"], self.valid_payload["parameters"])

    @patch("platform_backend_client.mip_logistic_regression.Experiment.run_transient")
    def test_run_from_nested_payload(self, mock_run_transient):
        nested_payload = {
            "name": "Nested payload",
            "mipVersion": "9.0.0",
            "algorithm": {
                "name": "logistic_regression",
                "parameters": {"positive_class": "M"},
                "preprocessing": {},
                "inputdata": {
                    "data_model": "dementia:0.1",
                    "datasets": ["edsd"],
                    "x": ["age_value"],
                    "y": ["gender"],
                    "filters": None,
                },
            },
        }
        result = {
            "dependent_var": "gender",
            "indep_vars": ["Intercept", "age_value"],
            "summary": {"coefficients": [0.2, 1.1]},
        }
        mock_run_transient.return_value = _ExperimentResponse(result=result)

        runner = FederatedLogisticRegression(nested_payload, auto_run=False)
        model = runner.fit()

        self.assertEqual(model.n_features_in_, 1)
        _, kwargs = mock_run_transient.call_args
        self.assertEqual(kwargs["algorithm_name"], "logistic_regression")
        self.assertEqual(kwargs["mip_version"], "9.0.0")

    @patch("platform_backend_client.mip_logistic_regression.Experiment.run_transient")
    def test_run_from_json_string(self, mock_run_transient):
        result = {
            "dependent_var": "gender",
            "indep_vars": ["Intercept", "age_value"],
            "summary": {"coefficients": [0.2, 1.1]},
        }
        mock_run_transient.return_value = _ExperimentResponse(result=result)

        payload_json = json.dumps(self.valid_payload)
        runner = FederatedLogisticRegression.from_json(payload_json, auto_run=False)
        model = runner.run()
        self.assertEqual(model.n_features_in_, 1)

    @patch("platform_backend_client.mip_logistic_regression.Experiment.run_transient")
    def test_prefers_sklearn_payload_when_present(self, mock_run_transient):
        result = {
            "sklearn": {
                "classes_": [0, 1],
                "coef_": [[0.7, -0.3]],
                "intercept_": [0.9],
                "n_features_in_": 2,
                "n_iter_": [15],
                "feature_names_in_": ["f1", "f2"],
            },
            "summary": {"coefficients": [99.0, 99.0, 99.0]},
        }
        mock_run_transient.return_value = _ExperimentResponse(result=result)

        runner = FederatedLogisticRegression(self.valid_payload, auto_run=False)
        model = runner.run()
        np.testing.assert_allclose(model.intercept_, np.asarray([0.9]))
        np.testing.assert_allclose(model.coef_, np.asarray([[0.7, -0.3]]))
        self.assertEqual(model.n_features_in_, 2)

    def test_rejects_non_logistic_algorithm_name(self):
        payload = dict(self.valid_payload)
        payload["algorithm_name"] = "linear_regression"
        with self.assertRaises(ValueError):
            FederatedLogisticRegression(payload)

    def test_rejects_missing_positive_class(self):
        payload = dict(self.valid_payload)
        payload["parameters"] = {}
        with self.assertRaises(ValueError):
            FederatedLogisticRegression(payload)

    def test_rejects_missing_required_fields(self):
        with self.assertRaises(ValueError):
            FederatedLogisticRegression({"name": "x"})

    @patch("platform_backend_client.mip_logistic_regression.Experiment.run_transient")
    def test_predict_methods_and_dump(self, mock_run_transient):
        result = {
            "dependent_var": "gender",
            "indep_vars": ["Intercept", "age_value", "education_level"],
            "summary": {
                "coefficients": [0.25, 1.5, -0.4],
            },
        }
        mock_run_transient.return_value = _ExperimentResponse(result=result)

        runner = FederatedLogisticRegression(self.valid_payload, auto_run=False)
        runner.run()
        x = np.zeros((2, 2), dtype=float)
        preds = runner.predict(x)
        probas = runner.predict_proba(x)

        self.assertEqual(len(preds), 2)
        self.assertEqual(probas.shape, (2, 2))

        fake_joblib = type(
            "FakeJoblib",
            (),
            {"dump": staticmethod(lambda model, path: path)},
        )
        with patch(
            "platform_backend_client.mip_logistic_regression.FederatedLogisticRegression._import_joblib",
            return_value=fake_joblib,
        ):
            with tempfile.NamedTemporaryFile(suffix=".joblib") as tmp:
                output = runner.dump(tmp.name)
                self.assertEqual(output, tmp.name)

    def test_predict_before_run_fails(self):
        runner = FederatedLogisticRegression(self.valid_payload, auto_run=False)
        with self.assertRaises(RuntimeError):
            runner.predict(np.zeros((1, 2), dtype=float))

    def test_predict_wraps_numpy_input_with_feature_names(self):
        class _FakeDataFrame:
            def __init__(self, data, columns):
                self._data = np.asarray(data)
                self.columns = list(columns)

            def __len__(self):
                return int(self._data.shape[0])

        class _CaptureModel:
            def __init__(self):
                self.feature_names_in_ = np.asarray(["age_value", "education_level"], dtype=object)

            def predict(self, x):
                if not isinstance(x, _FakeDataFrame):
                    raise AssertionError("Expected pandas DataFrame")
                if list(x.columns) != ["age_value", "education_level"]:
                    raise AssertionError(f"Unexpected columns: {list(x.columns)}")
                return np.zeros((len(x),), dtype=int)

            def predict_proba(self, x):
                if not isinstance(x, _FakeDataFrame):
                    raise AssertionError("Expected pandas DataFrame")
                if list(x.columns) != ["age_value", "education_level"]:
                    raise AssertionError(f"Unexpected columns: {list(x.columns)}")
                return np.zeros((len(x), 2), dtype=float)

        runner = FederatedLogisticRegression(self.valid_payload, auto_run=False)
        runner._model = _CaptureModel()

        x = np.zeros((3, 2), dtype=float)
        fake_pandas = types.SimpleNamespace(DataFrame=_FakeDataFrame)
        with patch.dict(sys.modules, {"pandas": fake_pandas}):
            preds = runner.predict(x)
            probas = runner.predict_proba(x)

        self.assertEqual(preds.shape, (3,))
        self.assertEqual(probas.shape, (3, 2))

    @patch("platform_backend_client.mip_logistic_regression.Experiment.run_transient")
    def test_exposes_native_model_attributes_and_methods(self, mock_run_transient):
        result = {
            "dependent_var": "gender",
            "indep_vars": ["Intercept", "age_value", "education_level"],
            "summary": {
                "coefficients": [0.25, 1.5, -0.4],
            },
        }
        mock_run_transient.return_value = _ExperimentResponse(result=result)

        runner = FederatedLogisticRegression(self.valid_payload, auto_run=False)
        runner.run()

        # Native estimator attributes are directly available via delegation.
        np.testing.assert_allclose(runner.coef_, np.asarray([[1.5, -0.4]]))
        np.testing.assert_array_equal(runner.classes_, np.asarray([0, 1]))

        # Native estimator methods are also available via delegation.
        x = np.zeros((2, 2), dtype=float)
        scores = runner.decision_function(x)
        self.assertEqual(scores.shape, (2,))

    @patch("platform_backend_client.mip_logistic_regression.Experiment.run_transient")
    def test_auto_run_on_init_by_default(self, mock_run_transient):
        result = {
            "dependent_var": "gender",
            "indep_vars": ["Intercept", "age_value", "education_level"],
            "summary": {"coefficients": [0.25, 1.5, -0.4]},
        }
        mock_run_transient.return_value = _ExperimentResponse(result=result)

        model = FederatedLogisticRegression(self.valid_payload)
        self.assertEqual(model.n_features_in_, 2)
        self.assertEqual(mock_run_transient.call_count, 1)


if __name__ == "__main__":
    unittest.main()
