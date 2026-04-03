"""High-level linear regression helper for notebook users.

This class accepts a transient experiment JSON payload, executes only the
`linear_regression` algorithm through Platform Backend, and returns a fitted
sklearn-compatible LinearRegression model.
"""

from __future__ import annotations

import json
from typing import Any
from typing import Dict
from typing import Optional

from .experiment import Experiment


class FederatedLinearRegression:
    """Run MIP linear regression from a transient experiment payload."""

    ALGORITHM_NAME = "linear_regression"

    def __init__(
        self,
        transient_experiment: Dict[str, Any] | str,
        auto_run: bool = True,
    ):
        self._request = self._normalize_request(transient_experiment)
        self._model = None
        self.experiment_uuid: Optional[str] = None
        self.status: Optional[str] = None
        if bool(auto_run):
            self.run()

    @classmethod
    def from_json(
        cls,
        transient_experiment: Dict[str, Any] | str,
        auto_run: bool = True,
    ) -> "FederatedLinearRegression":
        return cls(transient_experiment, auto_run=auto_run)

    @property
    def request(self) -> Dict[str, Any]:
        return dict(self._request)

    @property
    def model(self):
        return self._model

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        model = self._require_model()
        try:
            return getattr(model, name)
        except AttributeError as exc:
            raise AttributeError(
                f"'FederatedLinearRegression' has no attribute '{name}' "
                f"and underlying model '{type(model).__name__}' does not expose it."
            ) from exc

    def run(self):
        response = Experiment.run_transient(
            name=self._request["name"],
            algorithm_name=self.ALGORITHM_NAME,
            data_model=self._request["data_model"],
            datasets=self._request["datasets"],
            x=self._request["x"],
            y=self._request["y"],
            filters=self._request.get("filters"),
            parameters=self._request.get("parameters") or {},
            preprocessing=self._request.get("preprocessing") or {},
            mip_version=self._request.get("mip_version"),
        )
        self.experiment_uuid = response.uuid
        self.status = response.status
        self._model = self._build_model_from_result(response.results)
        return self._model

    def fit(self):
        return self.run()

    def predict(self, x):
        model = self._require_model()
        return model.predict(self._coerce_input_with_feature_names(model, x))

    def dump(self, path: str):
        joblib = self._import_joblib()
        joblib.dump(self._require_model(), path)
        return path

    @classmethod
    def _normalize_request(cls, payload: Dict[str, Any] | str) -> Dict[str, Any]:
        data = cls._to_dict(payload)
        if "algorithm" in data and isinstance(data["algorithm"], dict):
            normalized = cls._normalize_nested_payload(data)
        else:
            normalized = cls._normalize_flat_payload(data)
        cls._validate_request(normalized)
        return normalized

    @classmethod
    def _to_dict(cls, payload: Dict[str, Any] | str) -> Dict[str, Any]:
        if isinstance(payload, dict):
            return dict(payload)
        if isinstance(payload, str):
            try:
                loaded = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise ValueError("Transient experiment payload is not valid JSON.") from exc
            if not isinstance(loaded, dict):
                raise ValueError("Transient experiment JSON must decode to an object.")
            return loaded
        raise TypeError("Transient experiment payload must be a dict or JSON string.")

    @classmethod
    def _normalize_flat_payload(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "name": payload.get("name"),
            "data_model": payload.get("data_model"),
            "datasets": payload.get("datasets"),
            "x": payload.get("x"),
            "y": payload.get("y"),
            "filters": payload.get("filters"),
            "parameters": payload.get("parameters") or {},
            "preprocessing": payload.get("preprocessing") or {},
            "mip_version": payload.get("mip_version") or payload.get("mipVersion"),
            "algorithm_name": payload.get("algorithm_name"),
        }

    @classmethod
    def _normalize_nested_payload(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        algorithm = payload.get("algorithm") or {}
        if not isinstance(algorithm, dict):
            raise ValueError("Field 'algorithm' must be an object.")
        inputdata = algorithm.get("inputdata") or {}
        if not isinstance(inputdata, dict):
            raise ValueError("Field 'algorithm.inputdata' must be an object.")

        return {
            "name": payload.get("name"),
            "data_model": inputdata.get("data_model"),
            "datasets": inputdata.get("datasets"),
            "x": inputdata.get("x"),
            "y": inputdata.get("y"),
            "filters": inputdata.get("filters"),
            "parameters": algorithm.get("parameters") or {},
            "preprocessing": algorithm.get("preprocessing") or {},
            "mip_version": payload.get("mipVersion") or payload.get("mip_version"),
            "algorithm_name": algorithm.get("name"),
        }

    @classmethod
    def _validate_request(cls, request: Dict[str, Any]) -> None:
        algorithm_name = request.get("algorithm_name")
        if algorithm_name and algorithm_name != cls.ALGORITHM_NAME:
            raise ValueError(
                f"Only '{cls.ALGORITHM_NAME}' is supported by FederatedLinearRegression, "
                f"got '{algorithm_name}'."
            )

        if not request.get("name"):
            raise ValueError("Missing required field: name")
        if not request.get("data_model"):
            raise ValueError("Missing required field: data_model")

        datasets = request.get("datasets")
        if not isinstance(datasets, list) or not datasets:
            raise ValueError("Field 'datasets' must be a non-empty list.")

        y_vars = request.get("y")
        if not isinstance(y_vars, list) or len(y_vars) != 1:
            raise ValueError("Field 'y' must be a list with exactly one target variable.")

        x_vars = request.get("x")
        if not isinstance(x_vars, list) or not x_vars:
            raise ValueError("Field 'x' must be a non-empty list of covariates.")

        parameters = request.get("parameters")
        if not isinstance(parameters, dict):
            raise ValueError("Field 'parameters' must be an object.")

    @classmethod
    def _build_model_from_result(cls, result_payload: Any):
        np, linear_regression_cls = cls._import_numpy_and_sklearn()

        if not isinstance(result_payload, dict):
            raise TypeError(
                "Transient experiment result is not a JSON object; cannot build sklearn model."
            )

        sklearn_payload = (
            result_payload.get("sklearn")
            or result_payload.get("sklearn_model")
            or result_payload.get("sklearn_compatible")
        )
        if isinstance(sklearn_payload, dict) and "coef_" in sklearn_payload:
            return cls._build_model_from_sklearn_payload(
                payload=sklearn_payload,
                np=np,
                linear_regression_cls=linear_regression_cls,
            )

        coefficients = result_payload.get("coefficients") or []
        if not coefficients:
            summary = result_payload.get("summary") or {}
            coefficients = summary.get("coefficients") or []

        if len(coefficients) < 1:
            raise ValueError(
                "Could not reconstruct linear model from result: expected "
                "'coefficients' with intercept + feature coefficients."
            )

        model = linear_regression_cls()
        coef_arr = np.asarray(coefficients[1:], dtype=float).reshape(-1)
        intercept_arr = np.asarray([coefficients[0]], dtype=float).reshape(-1)
        model.coef_ = coef_arr
        model.intercept_ = float(intercept_arr[0]) if intercept_arr.size == 1 else intercept_arr
        model.n_features_in_ = int(coef_arr.shape[0])

        indep_vars = result_payload.get("indep_vars") or []
        if indep_vars and len(indep_vars) == model.n_features_in_ + 1:
            model.feature_names_in_ = np.asarray(indep_vars[1:], dtype=object)

        return model

    @classmethod
    def _build_model_from_sklearn_payload(
        cls,
        payload: Dict[str, Any],
        np,
        linear_regression_cls,
    ):
        model = linear_regression_cls()
        coef = np.asarray(payload["coef_"], dtype=float)
        if coef.ndim == 2 and coef.shape[0] == 1:
            coef = coef.reshape(-1)
        elif coef.ndim > 2:
            raise ValueError(f"Expected sklearn payload coef_ as 1D/2D array, got shape {coef.shape}")

        model.coef_ = coef
        intercept_arr = np.asarray(payload.get("intercept_", 0.0), dtype=float).reshape(-1)
        model.intercept_ = float(intercept_arr[0]) if intercept_arr.size == 1 else intercept_arr
        model.n_features_in_ = int(payload.get("n_features_in_", coef.shape[-1]))

        if "feature_names_in_" in payload:
            model.feature_names_in_ = np.asarray(payload["feature_names_in_"], dtype=object)

        return model

    @staticmethod
    def _import_numpy_and_sklearn():
        try:
            import numpy as np
            from sklearn.linear_model import LinearRegression
        except Exception as exc:
            raise RuntimeError(
                "FederatedLinearRegression requires numpy and scikit-learn in the environment."
            ) from exc
        return np, LinearRegression

    @staticmethod
    def _import_joblib():
        try:
            import joblib
        except Exception as exc:
            raise RuntimeError("FederatedLinearRegression.dump requires joblib to be installed.") from exc
        return joblib

    def _require_model(self):
        if self._model is None:
            raise RuntimeError("Model is not available yet. Call run() first.")
        return self._model

    @staticmethod
    def _coerce_input_with_feature_names(model, x):
        feature_names = getattr(model, "feature_names_in_", None)
        if feature_names is None:
            return x
        if hasattr(x, "columns"):
            return x
        try:
            import numpy as np
            import pandas as pd
        except Exception:
            return x
        try:
            arr = np.asarray(x)
        except Exception:
            return x
        if arr.ndim != 2:
            return x
        if arr.shape[1] != len(feature_names):
            return x
        try:
            return pd.DataFrame(arr, columns=list(feature_names))
        except Exception:
            return x
