import json
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from platform_backend_client import FederatedNaiveBayes


class _ExperimentResponse:
    def __init__(self, result):
        self.uuid = "exp-nb-123"
        self.status = "success"
        self.results = result


class _FakeGaussianNB:
    def predict_proba(self, x):
        x = np.asarray(x)
        n_rows = x.shape[0] if x.ndim >= 2 else 0
        n_classes = len(getattr(self, "classes_", []))
        if n_classes == 0:
            return np.zeros((n_rows, 0), dtype=float)
        return np.ones((n_rows, n_classes), dtype=float) / n_classes

    def predict(self, x):
        probs = self.predict_proba(x)
        if probs.shape[1] == 0:
            return np.asarray([], dtype=object)
        classes = np.asarray(self.classes_, dtype=object)
        return np.repeat(classes[0], probs.shape[0])


class _FakeCategoricalNB:
    def predict_proba(self, x):
        x = np.asarray(x)
        n_rows = x.shape[0] if x.ndim >= 2 else 0
        n_classes = len(getattr(self, "classes_", []))
        if n_classes == 0:
            return np.zeros((n_rows, 0), dtype=float)
        return np.ones((n_rows, n_classes), dtype=float) / n_classes

    def predict(self, x):
        probs = self.predict_proba(x)
        if probs.shape[1] == 0:
            return np.asarray([], dtype=object)
        classes = np.asarray(self.classes_, dtype=object)
        return np.repeat(classes[0], probs.shape[0])


class TestFederatedNaiveBayes(unittest.TestCase):
    def setUp(self):
        self.valid_payload = {
            "name": "Notebook naive bayes",
            "algorithm_name": "naive_bayes_gaussian",
            "data_model": "dementia:0.1",
            "datasets": ["edsd"],
            "x": ["age_value", "education_level"],
            "y": ["gender"],
            "parameters": {},
        }
        patcher = patch(
            "platform_backend_client.mip_naive_bayes.FederatedNaiveBayes._import_numpy_and_sklearn",
            return_value=(np, _FakeGaussianNB, _FakeCategoricalNB),
        )
        self._import_patcher = patcher
        self._import_patcher.start()
        self.addCleanup(self._import_patcher.stop)

    @patch("platform_backend_client.mip_naive_bayes.Experiment.run_transient")
    def test_run_gaussian_payload_returns_model(self, mock_run_transient):
        result = {
            "classes": ["F", "M"],
            "class_count": [7.0, 5.0],
            "class_prior": [0.58, 0.42],
            "theta": [[0.1, 0.2], [0.5, 0.8]],
            "var": [[1.1, 1.2], [0.9, 0.7]],
            "feature_names": ["age_value", "education_level"],
        }
        mock_run_transient.return_value = _ExperimentResponse(result=result)

        runner = FederatedNaiveBayes(self.valid_payload, auto_run=False)
        model = runner.run()

        self.assertEqual(runner.experiment_uuid, "exp-nb-123")
        self.assertEqual(runner.algorithm_name, "naive_bayes_gaussian")
        self.assertEqual(model.n_features_in_, 2)
        np.testing.assert_array_equal(model.classes_, np.asarray(["F", "M"], dtype=object))
        np.testing.assert_allclose(model.class_count_, np.asarray([7.0, 5.0]))
        np.testing.assert_allclose(model.theta_, np.asarray([[0.1, 0.2], [0.5, 0.8]]))

    @patch("platform_backend_client.mip_naive_bayes.Experiment.run_transient")
    def test_run_categorical_payload_returns_model(self, mock_run_transient):
        payload = dict(self.valid_payload)
        payload["algorithm_name"] = "naive_bayes_categorical"
        payload["x"] = ["gender"]

        result = {
            "classes": ["A", "B"],
            "class_count": [10.0, 8.0],
            "class_log_prior": [-0.59, -0.81],
            "feature_names": ["gender"],
            "categories": {"gender": ["F", "M"]},
            "category_count": {"gender": [[6.0, 4.0], [3.0, 5.0]]},
            "category_log_prob": {"gender": [[-0.4, -1.0], [-0.9, -0.5]]},
        }
        mock_run_transient.return_value = _ExperimentResponse(result=result)

        runner = FederatedNaiveBayes(payload, auto_run=False)
        model = runner.run()

        self.assertEqual(runner.algorithm_name, "naive_bayes_categorical")
        self.assertEqual(model.n_features_in_, 1)
        self.assertEqual(len(model.category_count_), 1)
        self.assertEqual(len(model.feature_log_prob_), 1)

    def test_alias_naive_bayes_defaults_to_gaussian(self):
        payload = dict(self.valid_payload)
        payload["algorithm_name"] = "naive_bayes"
        runner = FederatedNaiveBayes(payload, auto_run=False)
        self.assertEqual(runner.algorithm_name, "naive_bayes_gaussian")

    def test_rejects_unknown_algorithm(self):
        payload = dict(self.valid_payload)
        payload["algorithm_name"] = "naive_bayes_unknown"
        with self.assertRaises(ValueError):
            FederatedNaiveBayes(payload, auto_run=False)

    @patch("platform_backend_client.mip_naive_bayes.Experiment.run_transient")
    def test_run_from_json_string(self, mock_run_transient):
        result = {
            "classes": ["F", "M"],
            "class_count": [7.0, 5.0],
            "class_prior": [0.58, 0.42],
            "theta": [[0.1, 0.2], [0.5, 0.8]],
            "var": [[1.1, 1.2], [0.9, 0.7]],
            "feature_names": ["age_value", "education_level"],
        }
        mock_run_transient.return_value = _ExperimentResponse(result=result)

        payload_json = json.dumps(self.valid_payload)
        runner = FederatedNaiveBayes.from_json(payload_json, auto_run=False)
        model = runner.run()
        self.assertEqual(model.n_features_in_, 2)

    @patch("platform_backend_client.mip_naive_bayes.Experiment.run_transient")
    def test_predict_proba_and_dump(self, mock_run_transient):
        result = {
            "classes": ["F", "M"],
            "class_count": [7.0, 5.0],
            "class_prior": [0.58, 0.42],
            "theta": [[0.1, 0.2], [0.5, 0.8]],
            "var": [[1.1, 1.2], [0.9, 0.7]],
            "feature_names": ["age_value", "education_level"],
        }
        mock_run_transient.return_value = _ExperimentResponse(result=result)

        runner = FederatedNaiveBayes(self.valid_payload, auto_run=False)
        runner.run()
        x = np.zeros((3, 2), dtype=float)
        preds = runner.predict(x)
        probas = runner.predict_proba(x)
        self.assertEqual(preds.shape, (3,))
        self.assertEqual(probas.shape, (3, 2))

        fake_joblib = type(
            "FakeJoblib",
            (),
            {"dump": staticmethod(lambda model, path: path)},
        )
        with patch(
            "platform_backend_client.mip_naive_bayes.FederatedNaiveBayes._import_joblib",
            return_value=fake_joblib,
        ):
            with tempfile.NamedTemporaryFile(suffix=".joblib") as tmp:
                output = runner.dump(tmp.name)
                self.assertEqual(output, tmp.name)

    def test_predict_before_run_fails(self):
        runner = FederatedNaiveBayes(self.valid_payload, auto_run=False)
        with self.assertRaises(RuntimeError):
            runner.predict(np.zeros((1, 2), dtype=float))

    @patch("platform_backend_client.mip_naive_bayes.Experiment.run_transient")
    def test_auto_run_on_init_by_default(self, mock_run_transient):
        result = {
            "classes": ["F", "M"],
            "class_count": [7.0, 5.0],
            "class_prior": [0.58, 0.42],
            "theta": [[0.1, 0.2], [0.5, 0.8]],
            "var": [[1.1, 1.2], [0.9, 0.7]],
            "feature_names": ["age_value", "education_level"],
        }
        mock_run_transient.return_value = _ExperimentResponse(result=result)

        model = FederatedNaiveBayes(self.valid_payload)
        self.assertEqual(model.n_features_in_, 2)
        self.assertEqual(mock_run_transient.call_count, 1)


if __name__ == "__main__":
    unittest.main()
