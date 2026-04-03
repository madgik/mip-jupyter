"""High-level Naive Bayes helper for notebook users.

This class accepts a transient experiment JSON payload, executes
`naive_bayes_gaussian` or `naive_bayes_categorical` through Platform Backend,
and returns a fitted sklearn-compatible estimator.
"""

from __future__ import annotations

import json
from typing import Any
from typing import Dict
from typing import Optional

from .experiment import Experiment


class FederatedNaiveBayes:
    """Run MIP naive bayes from a transient experiment payload."""

    DEFAULT_ALGORITHM = "naive_bayes_gaussian"
    ALGORITHM_ALIASES = {
        "naive_bayes": DEFAULT_ALGORITHM,
    }
    ALLOWED_ALGORITHMS = {
        "naive_bayes_gaussian",
        "naive_bayes_categorical",
    }

    def __init__(
        self,
        transient_experiment: Dict[str, Any] | str,
        auto_run: bool = True,
    ):
        self._request = self._normalize_request(transient_experiment)
        self._model = None
        self._model_kind: Optional[str] = None
        self._categorical_levels: Dict[str, list] = {}
        self.experiment_uuid: Optional[str] = None
        self.status: Optional[str] = None
        if bool(auto_run):
            self.run()

    @classmethod
    def from_json(
        cls,
        transient_experiment: Dict[str, Any] | str,
        auto_run: bool = True,
    ) -> "FederatedNaiveBayes":
        return cls(transient_experiment, auto_run=auto_run)

    @property
    def request(self) -> Dict[str, Any]:
        return dict(self._request)

    @property
    def model(self):
        return self._model

    @property
    def algorithm_name(self) -> str:
        return str(self._request["algorithm_name"])

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        model = self._require_model()
        try:
            return getattr(model, name)
        except AttributeError as exc:
            raise AttributeError(
                f"'FederatedNaiveBayes' has no attribute '{name}' "
                f"and underlying model '{type(model).__name__}' does not expose it."
            ) from exc

    def run(self):
        response = Experiment.run_transient(
            name=self._request["name"],
            algorithm_name=self._request["algorithm_name"],
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
        model, model_kind, categorical_levels = self._build_model_from_result(
            response.results,
            algorithm_name=self._request["algorithm_name"],
        )
        self._model = model
        self._model_kind = model_kind
        self._categorical_levels = dict(categorical_levels or {})
        return self._model

    def fit(self):
        return self.run()

    def predict(self, x):
        model = self._require_model()
        prepared = self._prepare_input_for_prediction(model, x)
        return model.predict(prepared)

    def predict_proba(self, x):
        model = self._require_model()
        prepared = self._prepare_input_for_prediction(model, x)
        return model.predict_proba(prepared)

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
            "algorithm_name": payload.get("algorithm_name") or cls.DEFAULT_ALGORITHM,
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
            "algorithm_name": algorithm.get("name") or cls.DEFAULT_ALGORITHM,
        }

    @classmethod
    def _validate_request(cls, request: Dict[str, Any]) -> None:
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

        algorithm_name = str(request.get("algorithm_name") or cls.DEFAULT_ALGORITHM)
        algorithm_name = cls.ALGORITHM_ALIASES.get(algorithm_name, algorithm_name)
        if algorithm_name not in cls.ALLOWED_ALGORITHMS:
            allowed = ", ".join(sorted(cls.ALLOWED_ALGORITHMS | set(cls.ALGORITHM_ALIASES.keys())))
            raise ValueError(
                f"Unsupported naive bayes algorithm '{algorithm_name}'. "
                f"Allowed values: {allowed}."
            )
        request["algorithm_name"] = algorithm_name

    @classmethod
    def _build_model_from_result(
        cls,
        result_payload: Any,
        algorithm_name: str,
    ):
        np, gaussian_nb_cls, categorical_nb_cls = cls._import_numpy_and_sklearn()
        if not isinstance(result_payload, dict):
            raise TypeError(
                "Transient experiment result is not a JSON object; cannot build sklearn model."
            )

        sklearn_payload = (
            result_payload.get("sklearn")
            or result_payload.get("sklearn_model")
            or result_payload.get("sklearn_compatible")
        )
        if isinstance(sklearn_payload, dict):
            if "theta_" in sklearn_payload or "var_" in sklearn_payload:
                model = cls._build_gaussian_model_from_payload(
                    payload=sklearn_payload,
                    np=np,
                    gaussian_nb_cls=gaussian_nb_cls,
                    is_sklearn_payload=True,
                )
                return model, "gaussian", {}
            if "feature_log_prob_" in sklearn_payload or "category_count_" in sklearn_payload:
                model, levels = cls._build_categorical_model_from_payload(
                    payload=sklearn_payload,
                    np=np,
                    categorical_nb_cls=categorical_nb_cls,
                    is_sklearn_payload=True,
                )
                return model, "categorical", levels

        if "theta" in result_payload and "var" in result_payload:
            model = cls._build_gaussian_model_from_payload(
                payload=result_payload,
                np=np,
                gaussian_nb_cls=gaussian_nb_cls,
                is_sklearn_payload=False,
            )
            return model, "gaussian", {}

        if "category_count" in result_payload or "category_log_prob" in result_payload:
            model, levels = cls._build_categorical_model_from_payload(
                payload=result_payload,
                np=np,
                categorical_nb_cls=categorical_nb_cls,
                is_sklearn_payload=False,
            )
            return model, "categorical", levels

        raise ValueError(
            f"Could not reconstruct naive bayes model from result for algorithm '{algorithm_name}'."
        )

    @classmethod
    def _build_gaussian_model_from_payload(
        cls,
        payload: Dict[str, Any],
        np,
        gaussian_nb_cls,
        is_sklearn_payload: bool,
    ):
        model = gaussian_nb_cls()
        classes = np.asarray(payload.get("classes_" if is_sklearn_payload else "classes", []), dtype=object)
        theta = np.asarray(payload.get("theta_" if is_sklearn_payload else "theta", []), dtype=float)
        var = np.asarray(payload.get("var_" if is_sklearn_payload else "var", []), dtype=float)
        if theta.ndim != 2 or var.ndim != 2 or theta.shape != var.shape:
            raise ValueError(
                "Naive bayes gaussian payload must include 2D 'theta' and 'var' arrays with same shape."
            )

        class_count = np.asarray(
            payload.get("class_count_" if is_sklearn_payload else "class_count", []),
            dtype=float,
        )
        class_prior = np.asarray(
            payload.get("class_prior_" if is_sklearn_payload else "class_prior", []),
            dtype=float,
        )

        if class_count.size == 0 and classes.size:
            class_count = np.ones(classes.size, dtype=float)
        if class_prior.size == 0 and class_count.size:
            total = class_count.sum()
            class_prior = class_count / total if total > 0 else np.ones_like(class_count) / len(class_count)

        model.classes_ = classes
        model.class_count_ = class_count
        model.class_prior_ = class_prior
        model.theta_ = theta
        model.var_ = var
        model.epsilon_ = float(payload.get("epsilon_", 0.0 if is_sklearn_payload else 1e-9))
        model.n_features_in_ = int(payload.get("n_features_in_", theta.shape[1]))

        feature_names_key = "feature_names_in_" if is_sklearn_payload else "feature_names"
        feature_names = payload.get(feature_names_key) or []
        if feature_names and len(feature_names) == model.n_features_in_:
            model.feature_names_in_ = np.asarray(feature_names, dtype=object)

        return model

    @classmethod
    def _build_categorical_model_from_payload(
        cls,
        payload: Dict[str, Any],
        np,
        categorical_nb_cls,
        is_sklearn_payload: bool,
    ):
        model = categorical_nb_cls()
        classes = np.asarray(payload.get("classes_" if is_sklearn_payload else "classes", []), dtype=object)
        class_count = np.asarray(
            payload.get("class_count_" if is_sklearn_payload else "class_count", []),
            dtype=float,
        )
        class_log_prior = np.asarray(
            payload.get("class_log_prior_" if is_sklearn_payload else "class_log_prior", []),
            dtype=float,
        )

        feature_names = payload.get("feature_names_in_" if is_sklearn_payload else "feature_names") or []
        raw_category_count = payload.get("category_count_" if is_sklearn_payload else "category_count")
        raw_feature_log_prob = payload.get("feature_log_prob_" if is_sklearn_payload else "category_log_prob")
        raw_categories = payload.get("categories")

        if not feature_names:
            if isinstance(raw_category_count, dict):
                feature_names = list(raw_category_count.keys())
            elif isinstance(raw_feature_log_prob, dict):
                feature_names = list(raw_feature_log_prob.keys())
            elif isinstance(raw_categories, dict):
                feature_names = list(raw_categories.keys())

        category_count = cls._ordered_feature_matrices(raw_category_count, feature_names, np, "category_count")
        feature_log_prob = cls._ordered_feature_matrices(
            raw_feature_log_prob,
            feature_names,
            np,
            "category_log_prob",
        )

        if not feature_names:
            feature_names = [f"x{i}" for i in range(len(category_count))]

        categories_levels = cls._normalize_categories(raw_categories, feature_names)

        if class_count.size == 0 and classes.size:
            class_count = np.ones(classes.size, dtype=float)
        if class_log_prior.size == 0 and class_count.size:
            prior = class_count / class_count.sum() if class_count.sum() > 0 else np.ones_like(class_count) / len(class_count)
            class_log_prior = np.log(prior)

        model.classes_ = classes
        model.class_count_ = class_count
        model.class_log_prior_ = class_log_prior
        model.category_count_ = category_count
        model.feature_log_prob_ = feature_log_prob
        model.n_features_in_ = int(payload.get("n_features_in_", len(feature_names)))
        model.n_categories_ = np.asarray(
            [int(arr.shape[1]) if arr.ndim == 2 else 0 for arr in model.category_count_],
            dtype=np.int64,
        )
        if feature_names and len(feature_names) == model.n_features_in_:
            model.feature_names_in_ = np.asarray(feature_names, dtype=object)

        return model, categories_levels

    @staticmethod
    def _ordered_feature_matrices(raw_value: Any, feature_names, np, field_name: str):
        if raw_value is None:
            return []
        if isinstance(raw_value, dict):
            if not feature_names:
                feature_names = list(raw_value.keys())
            matrices = [np.asarray(raw_value.get(name, []), dtype=float) for name in feature_names]
        elif isinstance(raw_value, list):
            matrices = [np.asarray(item, dtype=float) for item in raw_value]
        else:
            raise ValueError(f"Field '{field_name}' must be either a list or an object.")
        return matrices

    @staticmethod
    def _normalize_categories(raw_categories: Any, feature_names):
        if isinstance(raw_categories, dict):
            return {name: list(raw_categories.get(name, [])) for name in feature_names}
        if isinstance(raw_categories, list):
            return {
                feature_names[idx]: list(levels)
                for idx, levels in enumerate(raw_categories[: len(feature_names)])
            }
        return {}

    @staticmethod
    def _import_numpy_and_sklearn():
        try:
            import numpy as np
            from sklearn.naive_bayes import CategoricalNB
            from sklearn.naive_bayes import GaussianNB
        except Exception as exc:
            raise RuntimeError(
                "FederatedNaiveBayes requires numpy and scikit-learn in the environment."
            ) from exc
        return np, GaussianNB, CategoricalNB

    @staticmethod
    def _import_joblib():
        try:
            import joblib
        except Exception as exc:
            raise RuntimeError("FederatedNaiveBayes.dump requires joblib to be installed.") from exc
        return joblib

    def _require_model(self):
        if self._model is None:
            raise RuntimeError("Model is not available yet. Call run() first.")
        return self._model

    def _prepare_input_for_prediction(self, model, x):
        if self._model_kind == "categorical":
            return self._coerce_categorical_input(model, x, self._categorical_levels)
        return self._coerce_input_with_feature_names(model, x)

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

    @staticmethod
    def _coerce_categorical_input(model, x, categorical_levels):
        try:
            import numpy as np
            import pandas as pd
        except Exception:
            return x

        feature_names = list(getattr(model, "feature_names_in_", []))
        if not feature_names:
            feature_names = [f"x{i}" for i in range(int(getattr(model, "n_features_in_", 0)))]

        if hasattr(x, "columns"):
            try:
                df = x.loc[:, feature_names].copy()
            except Exception:
                df = x.copy()
                missing_cols = [c for c in feature_names if c not in list(df.columns)]
                if missing_cols:
                    raise ValueError(f"Missing required feature columns: {missing_cols}")

            for feat_name in feature_names:
                levels = list(categorical_levels.get(feat_name, []))
                if not levels:
                    df[feat_name] = pd.to_numeric(df[feat_name], errors="raise").astype(int)
                    continue

                level_to_code = {str(level): idx for idx, level in enumerate(levels)}
                col = df[feat_name]
                if np.issubdtype(col.dtype, np.number):
                    df[feat_name] = pd.to_numeric(col, errors="raise").astype(int)
                    continue

                mapped = col.astype(str).map(level_to_code)
                unknown_mask = mapped.isna() & col.notna()
                if bool(unknown_mask.any()):
                    unknown_values = col[unknown_mask].astype(str).unique().tolist()
                    raise ValueError(
                        f"Unknown category values for feature '{feat_name}': {unknown_values}. "
                        f"Known values: {levels}."
                    )
                df[feat_name] = mapped.fillna(0).astype(int)

            return df

        arr = np.asarray(x)
        if arr.ndim == 1:
            n_features = int(getattr(model, "n_features_in_", 0))
            if n_features > 0 and arr.size % n_features == 0:
                arr = arr.reshape(-1, n_features)
        if arr.ndim != 2:
            return x
        try:
            return arr.astype(int, copy=False)
        except Exception:
            return x
