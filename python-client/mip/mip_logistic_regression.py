"""High-level logistic regression helper for notebook users.

This module executes `logistic_regression` through Platform Backend and keeps
the raw transient result as the primary output. Sklearn reconstruction is now
explicit via `.get_sklearn_params()` and optional manual materialization.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import Optional

from .experiment import Experiment

_SKLEARN_LOGISTIC_SETTABLE_PARAMS = {
    "C",
    "class_weight",
    "dual",
    "fit_intercept",
    "intercept_scaling",
    "l1_ratio",
    "max_iter",
    "multi_class",
    "n_jobs",
    "penalty",
    "random_state",
    "solver",
    "tol",
    "verbose",
    "warm_start",
}

_SKLEARN_LOGISTIC_FITTED_ATTRIBUTES = {
    "classes_",
    "coef_",
    "feature_names_in_",
    "intercept_",
    "n_features_in_",
    "n_iter_",
}


@dataclass
class FederatedLogisticRegressionResult:
    """Result container returned by federated logistic runs."""

    experiment_uuid: Optional[str]
    status: Optional[str]
    payload: Dict[str, Any]
    request: Dict[str, Any]

    def get_sklearn_params(self) -> Dict[str, Any]:
        """Return sklearn-compatible parameter bundles.

        Returns:
            {
                "set_params": {...},        # safe for LogisticRegression.set_params
                "fitted_attributes": {...}, # coef_/intercept_/classes_/...
            }
        """
        return FederatedLogisticRegression._extract_sklearn_params(self.payload)

    def to_sklearn_model(self):
        """Materialize an sklearn LogisticRegression from this result."""
        sklearn_params = self.get_sklearn_params()
        return FederatedLogisticRegression._materialize_sklearn_model(sklearn_params)


class FederatedLogisticRegression:
    """Run MIP logistic regression from a transient experiment payload.

    Supported input payloads:
    - Flat shape (close to `Experiment.run_transient` kwargs)
    - Nested shape (close to backend transient endpoint JSON body)

    By default, construction triggers execution immediately:
        result = FederatedLogisticRegression(payload)
        params = result.get_sklearn_params()

    Set `auto_run=False` if you want explicit control and call `run()` later.
    """

    ALGORITHM_NAME = "logistic_regression"

    def __init__(
        self,
        transient_experiment: Dict[str, Any] | str,
        auto_run: bool = True,
    ):
        self._request = self._normalize_request(transient_experiment)
        self._result: Optional[FederatedLogisticRegressionResult] = None
        self._model_cache = None
        self.experiment_uuid: Optional[str] = None
        self.status: Optional[str] = None
        if bool(auto_run):
            self.run()

    @classmethod
    def from_json(
        cls,
        transient_experiment: Dict[str, Any] | str,
        auto_run: bool = True,
    ) -> "FederatedLogisticRegression":
        """Factory alias that accepts dict or JSON string."""
        return cls(transient_experiment, auto_run=auto_run)

    @property
    def request(self) -> Dict[str, Any]:
        """Return the normalized transient request payload."""
        return dict(self._request)

    @property
    def result(self) -> FederatedLogisticRegressionResult:
        """Return the raw federated result object after run()."""
        return self._require_result()

    @property
    def results(self) -> Dict[str, Any]:
        """Return a copy of the raw backend result payload."""
        return dict(self._require_result().payload)

    @property
    def model(self):
        """Lazily materialize a local sklearn model from the raw result."""
        return self.to_sklearn_model()

    def run(self) -> FederatedLogisticRegressionResult:
        """Execute transient logistic regression and keep raw backend results."""
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

        if not isinstance(response.results, dict):
            raise TypeError(
                "Transient experiment result is not a JSON object; cannot extract sklearn params."
            )

        self._result = FederatedLogisticRegressionResult(
            experiment_uuid=response.uuid,
            status=response.status,
            payload=dict(response.results),
            request=dict(self._request),
        )
        self._model_cache = None
        return self._result

    def fit(self) -> FederatedLogisticRegressionResult:
        """Alias for run() to mirror sklearn naming."""
        return self.run()

    def get_sklearn_params(self) -> Dict[str, Any]:
        """Return sklearn parameter bundles from the raw federated result."""
        return self._require_result().get_sklearn_params()

    def to_sklearn_model(self, refresh: bool = False):
        """Materialize a local sklearn LogisticRegression model on demand."""
        if self._model_cache is None or bool(refresh):
            self._model_cache = self._require_result().to_sklearn_model()
        return self._model_cache

    def predict(self, x):
        """Predict classes using an on-demand materialized sklearn model."""
        model = self.to_sklearn_model()
        return model.predict(self._coerce_input_with_feature_names(model, x))

    def predict_proba(self, x):
        """Predict probabilities using an on-demand materialized sklearn model."""
        model = self.to_sklearn_model()
        return model.predict_proba(self._coerce_input_with_feature_names(model, x))

    def dump(self, path: str):
        """Persist the materialized sklearn model to disk via joblib."""
        joblib = self._import_joblib()
        joblib.dump(self.to_sklearn_model(), path)
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
                f"Only '{cls.ALGORITHM_NAME}' is supported by FederatedLogisticRegression, "
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
        if "positive_class" not in parameters:
            raise ValueError(
                "Field 'parameters.positive_class' is required for logistic_regression."
            )

    @classmethod
    def _extract_sklearn_params(cls, result_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract sklearn-compatible params from backend result payload."""
        if not isinstance(result_payload, dict):
            raise TypeError(
                "Transient experiment result is not a JSON object; cannot extract sklearn params."
            )

        sklearn_payload = (
            result_payload.get("sklearn")
            or result_payload.get("sklearn_model")
            or result_payload.get("sklearn_compatible")
        )

        if isinstance(sklearn_payload, dict):
            return cls._extract_from_sklearn_payload(sklearn_payload)

        return cls._extract_from_summary_payload(result_payload)

    @classmethod
    def _extract_from_sklearn_payload(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        fitted_attributes: Dict[str, Any] = {}
        for key in _SKLEARN_LOGISTIC_FITTED_ATTRIBUTES:
            if key in payload:
                fitted_attributes[key] = payload[key]

        if "coef_" not in fitted_attributes or "intercept_" not in fitted_attributes:
            raise ValueError(
                "Sklearn payload must include 'coef_' and 'intercept_' to reconstruct model parameters."
            )

        coef_rows, coef_cols = cls._infer_coef_shape(fitted_attributes["coef_"])
        if coef_cols <= 0:
            raise ValueError("Sklearn payload 'coef_' must contain at least one feature coefficient.")

        if "classes_" not in fitted_attributes:
            fitted_attributes["classes_"] = [0, 1] if coef_rows <= 1 else list(range(coef_rows))
        if "n_features_in_" not in fitted_attributes:
            fitted_attributes["n_features_in_"] = int(coef_cols)
        if "n_iter_" not in fitted_attributes:
            fitted_attributes["n_iter_"] = [1]

        set_params = {}
        nested_set_params = payload.get("set_params")
        if isinstance(nested_set_params, dict):
            set_params.update(nested_set_params)
        for key in _SKLEARN_LOGISTIC_SETTABLE_PARAMS:
            if key in payload:
                set_params[key] = payload[key]

        return {
            "set_params": set_params,
            "fitted_attributes": fitted_attributes,
        }

    @classmethod
    def _extract_from_summary_payload(cls, result_payload: Dict[str, Any]) -> Dict[str, Any]:
        summary = result_payload.get("summary") or {}
        coefficients = summary.get("coefficients") or []
        indep_vars = result_payload.get("indep_vars") or []
        if len(coefficients) < 2:
            raise ValueError(
                "Could not extract sklearn parameters from result: "
                "expected summary.coefficients with intercept + feature coefficients."
            )

        fitted_attributes: Dict[str, Any] = {
            "classes_": [0, 1],
            "intercept_": [coefficients[0]],
            "coef_": [coefficients[1:]],
            "n_features_in_": len(coefficients) - 1,
            "n_iter_": [1],
        }
        if indep_vars and len(indep_vars) == len(coefficients):
            fitted_attributes["feature_names_in_"] = list(indep_vars[1:])

        return {
            "set_params": {},
            "fitted_attributes": fitted_attributes,
        }

    @staticmethod
    def _infer_coef_shape(coef: Any) -> tuple[int, int]:
        shape = getattr(coef, "shape", None)
        if isinstance(shape, tuple) and len(shape) == 2:
            return int(shape[0]), int(shape[1])

        if isinstance(coef, (list, tuple)):
            if not coef:
                return 0, 0
            first = coef[0]
            if isinstance(first, (list, tuple)):
                return len(coef), len(first)
            return 1, len(coef)

        return 0, 0

    @classmethod
    def _materialize_sklearn_model(cls, sklearn_params: Dict[str, Any]):
        np, logistic_regression_cls = cls._import_numpy_and_sklearn()

        set_params = sklearn_params.get("set_params") or {}
        fitted_attributes = sklearn_params.get("fitted_attributes") or {}

        model = logistic_regression_cls()
        if set_params:
            model = model.set_params(**set_params)

        required = {"coef_", "intercept_", "classes_"}
        missing = sorted(required - set(fitted_attributes.keys()))
        if missing:
            raise ValueError(
                f"Cannot materialize sklearn model; missing fitted attributes: {', '.join(missing)}."
            )

        coef = np.asarray(fitted_attributes["coef_"], dtype=float)
        if coef.ndim == 1:
            coef = coef.reshape(1, -1)
        if coef.ndim != 2:
            raise ValueError(f"Expected fitted coef_ as 2D array-like, got shape {coef.shape}.")

        model.coef_ = coef
        model.intercept_ = np.asarray(fitted_attributes["intercept_"], dtype=float).reshape(-1)
        model.classes_ = np.asarray(fitted_attributes["classes_"])
        model.n_features_in_ = int(fitted_attributes.get("n_features_in_", coef.shape[1]))
        model.n_iter_ = np.asarray(fitted_attributes.get("n_iter_", [1]), dtype=np.int32)

        if "feature_names_in_" in fitted_attributes:
            model.feature_names_in_ = np.asarray(fitted_attributes["feature_names_in_"], dtype=object)

        return model

    @staticmethod
    def _import_numpy_and_sklearn():
        try:
            import numpy as np
            from sklearn.linear_model import LogisticRegression
        except Exception as exc:
            raise RuntimeError(
                "FederatedLogisticRegression requires numpy and scikit-learn in the environment."
            ) from exc
        return np, LogisticRegression

    @staticmethod
    def _import_joblib():
        try:
            import joblib
        except Exception as exc:
            raise RuntimeError("FederatedLogisticRegression.dump requires joblib to be installed.") from exc
        return joblib

    def _require_result(self) -> FederatedLogisticRegressionResult:
        if self._result is None:
            raise RuntimeError("Result is not available yet. Call run() first.")
        return self._result

    @staticmethod
    def _coerce_input_with_feature_names(model, x):
        """Wrap ndarray-like inputs into a DataFrame when feature names exist.

        This avoids sklearn warnings about missing feature names and keeps
        column-to-coefficient alignment explicit.
        """
        feature_names = getattr(model, "feature_names_in_", None)
        if feature_names is None:
            return x

        # If input is already a DataFrame-like object with columns, keep it.
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
