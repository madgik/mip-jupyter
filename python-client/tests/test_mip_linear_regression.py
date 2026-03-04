import json
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from platform_backend_client import FederatedLinearRegression


class _ExperimentResponse:
    def __init__(self, result):
        self.uuid = "exp-lin-123"
        self.status = "success"
        self.results = result


class _FakeLinearRegression:
    def predict(self, x):
        x = np.asarray(x, dtype=float)
        coef = np.asarray(self.coef_, dtype=float).reshape(-1)
        return x @ coef + float(self.intercept_)


class TestFederatedLinearRegression(unittest.TestCase):
    def setUp(self):
        self.valid_payload = {
            "name": "Notebook linear regression",
            "data_model": "dementia:0.1",
            "datasets": ["edsd"],
            "x": ["age_value", "education_level"],
            "y": ["rightocpoccipitalpole"],
            "parameters": {},
        }
        patcher = patch(
            "platform_backend_client.mip_linear_regression.FederatedLinearRegression._import_numpy_and_sklearn",
            return_value=(np, _FakeLinearRegression),
        )
        self._import_patcher = patcher
        self._import_patcher.start()
        self.addCleanup(self._import_patcher.stop)

    @patch("platform_backend_client.mip_linear_regression.Experiment.run_transient")
    def test_run_from_linear_payload_returns_model(self, mock_run_transient):
        result = {
            "dependent_var": "rightocpoccipitalpole",
            "indep_vars": ["Intercept", "age_value", "education_level"],
            "coefficients": [0.5, 1.2, -0.3],
        }
        mock_run_transient.return_value = _ExperimentResponse(result=result)

        runner = FederatedLinearRegression(self.valid_payload, auto_run=False)
        model = runner.run()

        self.assertEqual(runner.experiment_uuid, "exp-lin-123")
        self.assertEqual(model.n_features_in_, 2)
        np.testing.assert_allclose(model.intercept_, 0.5)
        np.testing.assert_allclose(model.coef_, np.asarray([1.2, -0.3]))

        _, kwargs = mock_run_transient.call_args
        self.assertEqual(kwargs["algorithm_name"], "linear_regression")
        self.assertEqual(kwargs["name"], self.valid_payload["name"])

    @patch("platform_backend_client.mip_linear_regression.Experiment.run_transient")
    def test_prefers_sklearn_payload_when_present(self, mock_run_transient):
        result = {
            "sklearn": {
                "coef_": [0.7, -0.2],
                "intercept_": 1.1,
                "n_features_in_": 2,
                "feature_names_in_": ["f1", "f2"],
            },
            "coefficients": [99.0, 99.0, 99.0],
        }
        mock_run_transient.return_value = _ExperimentResponse(result=result)

        runner = FederatedLinearRegression(self.valid_payload, auto_run=False)
        model = runner.run()

        np.testing.assert_allclose(model.coef_, np.asarray([0.7, -0.2]))
        np.testing.assert_allclose(model.intercept_, 1.1)
        self.assertEqual(model.n_features_in_, 2)

    @patch("platform_backend_client.mip_linear_regression.Experiment.run_transient")
    def test_run_from_json_string(self, mock_run_transient):
        result = {
            "indep_vars": ["Intercept", "age_value"],
            "coefficients": [0.2, 1.1],
        }
        mock_run_transient.return_value = _ExperimentResponse(result=result)

        payload_json = json.dumps(self.valid_payload)
        runner = FederatedLinearRegression.from_json(payload_json, auto_run=False)
        model = runner.run()
        self.assertEqual(model.n_features_in_, 1)

    def test_rejects_non_linear_algorithm_name(self):
        payload = dict(self.valid_payload)
        payload["algorithm_name"] = "logistic_regression"
        with self.assertRaises(ValueError):
            FederatedLinearRegression(payload)

    def test_rejects_missing_required_fields(self):
        with self.assertRaises(ValueError):
            FederatedLinearRegression({"name": "x"})

    @patch("platform_backend_client.mip_linear_regression.Experiment.run_transient")
    def test_predict_and_dump(self, mock_run_transient):
        result = {
            "indep_vars": ["Intercept", "age_value", "education_level"],
            "coefficients": [0.25, 1.5, -0.4],
        }
        mock_run_transient.return_value = _ExperimentResponse(result=result)

        runner = FederatedLinearRegression(self.valid_payload, auto_run=False)
        runner.run()
        x = np.zeros((2, 2), dtype=float)
        preds = runner.predict(x)
        self.assertEqual(preds.shape, (2,))

        fake_joblib = type(
            "FakeJoblib",
            (),
            {"dump": staticmethod(lambda model, path: path)},
        )
        with patch(
            "platform_backend_client.mip_linear_regression.FederatedLinearRegression._import_joblib",
            return_value=fake_joblib,
        ):
            with tempfile.NamedTemporaryFile(suffix=".joblib") as tmp:
                output = runner.dump(tmp.name)
                self.assertEqual(output, tmp.name)

    def test_predict_before_run_fails(self):
        runner = FederatedLinearRegression(self.valid_payload, auto_run=False)
        with self.assertRaises(RuntimeError):
            runner.predict(np.zeros((1, 2), dtype=float))

    @patch("platform_backend_client.mip_linear_regression.Experiment.run_transient")
    def test_auto_run_on_init_by_default(self, mock_run_transient):
        result = {
            "indep_vars": ["Intercept", "age_value", "education_level"],
            "coefficients": [0.25, 1.5, -0.4],
        }
        mock_run_transient.return_value = _ExperimentResponse(result=result)

        model = FederatedLinearRegression(self.valid_payload)
        self.assertEqual(model.n_features_in_, 2)
        self.assertEqual(mock_run_transient.call_count, 1)


if __name__ == "__main__":
    unittest.main()
