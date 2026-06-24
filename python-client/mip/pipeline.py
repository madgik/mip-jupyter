"""Fixed-order analysis pipeline and algorithm execution."""

from __future__ import annotations

from typing import Any
from typing import Sequence

from .exceptions import MipBackendError
from .request_builder import build_experiment_payload
from .request_builder import code as _code
from .results import ModelResult
from .results import Result


class Pipeline:
    """Analysis execution pipeline with fixed filters/preprocessing order."""

    def __init__(
        self,
        *,
        analysis_set,
        filters=None,
        handle_missing=None,
        outlier_handling=None,
        new_columns: Sequence[Any] | None = None,
    ):
        self.analysis_set = analysis_set
        self.filters = filters
        self.handle_missing = handle_missing
        self.outlier_handling = outlier_handling
        self.new_columns = list(new_columns or [])

    def describe(self, mode: str = "transient") -> Result:
        return self._execute_algorithm(
            "describe",
            algorithm_y=self.analysis_set.variables,
            parameters={},
            mode=mode,
            name_for_ui="Describe",
        )

    def histogram(self, variable: Any, bins: int | None = None, mode: str = "transient") -> Result:
        parameters = {}
        if bins is not None:
            parameters["bins"] = bins
        return self._execute_algorithm(
            "histogram",
            algorithm_y=[variable],
            parameters=parameters,
            mode=mode,
            name_for_ui=f"Histogram: {_code(variable)}",
            result_type="histogram",
        )

    def t_test(
        self,
        *,
        variable: Any,
        group_by: Any,
        group_a: Any,
        group_b: Any,
        alt_hypothesis: str = "two-sided",
        alpha: float = 0.05,
        mode: str = "transient",
    ) -> Result:
        return self._execute_algorithm(
            "ttest_independent",
            algorithm_x=[group_by],
            algorithm_y=[variable],
            parameters={
                "alt_hypothesis": alt_hypothesis,
                "alpha": alpha,
                "groupA": group_a,
                "groupB": group_b,
            },
            mode=mode,
            name_for_ui=f"T-test: {_code(variable)}",
        )

    def pearson_correlation(self, *, x: Any, y: Any, mode: str = "transient") -> Result:
        return self._execute_algorithm(
            "pearson_correlation",
            algorithm_x=[x],
            algorithm_y=[y],
            parameters={},
            mode=mode,
            name_for_ui=f"Pearson correlation: {_code(x)} vs {_code(y)}",
        )

    def chi_square_test(self, *, x: Any, y: Any, mode: str = "transient") -> Result:
        return self._execute_algorithm(
            "chi_squared",
            algorithm_x=[x],
            algorithm_y=[y],
            parameters={},
            mode=mode,
            name_for_ui=f"Chi-square test: {_code(x)} vs {_code(y)}",
        )

    def logistic_regression(
        self,
        *,
        x: Sequence[Any],
        y: Any,
        positive_class: Any,
        mode: str = "transient",
    ) -> ModelResult:
        return self._execute_algorithm(
            "logistic_regression",
            algorithm_x=list(x),
            algorithm_y=[y],
            parameters={"positive_class": positive_class},
            mode=mode,
            name_for_ui=f"Logistic regression: {_code(y)}",
            result_class=ModelResult,
            result_type="logistic_regression",
            result_kwargs={"positive_class": positive_class},
        )

    def summary(self) -> dict[str, Any]:
        return {
            "analysis_set": self.analysis_set.summary(),
            "filters": self._filters_payload(),
            "preprocessing": self._preprocessing_payload(),
            "new_columns": [step.summary() for step in self.new_columns],
        }

    def explain(self) -> dict[str, Any]:
        return self.summary()

    def available_algorithms(self) -> list[str]:
        return [
            "describe",
            "histogram",
            "t_test",
            "pearson_correlation",
            "chi_square_test",
            "logistic_regression",
        ]

    def recommend_algorithms(self) -> str:
        from .display import recommend_pipeline_steps

        return recommend_pipeline_steps(self.analysis_set.variables)

    def _repr_html_(self) -> str:
        from .display import render_object_card

        summary = self.summary()
        return render_object_card(
            "Pipeline",
            {
                "data_model": summary["analysis_set"]["data_model"],
                "variables": ", ".join(summary["analysis_set"]["variables"]),
                "filters": "yes" if self.filters is not None else "no",
                "preprocessing": "yes" if summary.get("preprocessing") else "no",
            },
            [
                ".explain()",
                ".recommend_algorithms()",
                ".histogram(variable=...)",
                ".help()",
            ],
        )

    def help(self) -> str:
        from .display import show_help

        return show_help("Pipeline")

    def _execute_algorithm(
        self,
        name: str,
        *,
        algorithm_x: Sequence[Any] | None = None,
        algorithm_y: Sequence[Any] | None = None,
        parameters: dict,
        mode: str,
        name_for_ui: str | None = None,
        description: str | None = None,
        result_class=Result,
        result_type: str | None = None,
        result_kwargs: dict[str, Any] | None = None,
    ):
        payload = build_experiment_payload(
            name=name_for_ui or name,
            data_model_name=self.analysis_set.data_model_name(),
            datasets=self.analysis_set.datasets,
            analysis_set_variables=self.analysis_set.variables,
            filters=self.filters,
            handle_missing=self.handle_missing,
            outlier_handling=self.outlier_handling,
            new_columns=self.new_columns,
            algorithm_name=name,
            algorithm_x=algorithm_x,
            algorithm_y=algorithm_y,
            parameters=parameters or {},
        )
        if description:
            payload["description"] = description

        transport = self.analysis_set._require_transport()
        endpoint = "/experiments/transient" if mode == "transient" else "/experiments" if mode == "persisted" else None
        if endpoint is None:
            raise ValueError("mode must be 'transient' or 'persisted'.")
        response = transport.post(endpoint, payload)
        raw = _extract_result(response)
        _raise_for_experiment_error(response, raw)
        kwargs = dict(result_kwargs or {})
        return result_class(raw=raw, payload=response, result_type=result_type or name, **kwargs)

    def _filters_payload(self):
        if self.filters is None:
            return None
        if hasattr(self.filters, "explain"):
            return self.filters.explain()
        return self.filters

    def _preprocessing_payload(self) -> list[dict[str, Any]] | None:
        from .request_builder import build_preprocessing_steps

        return build_preprocessing_steps(
            handle_missing=self.handle_missing,
            outlier_handling=self.outlier_handling,
            new_columns=self.new_columns,
        )


def _extract_result(response: Any) -> Any:
    if isinstance(response, dict):
        if "result" in response:
            return response.get("result")
        if "results" in response:
            return response.get("results")
    return response


def _raise_for_experiment_error(response: Any, raw: Any) -> None:
    if not isinstance(response, dict):
        return
    status = str(response.get("status") or "").strip().lower()
    error = response.get("errorMessage") or response.get("error")
    if not error and isinstance(raw, dict):
        error = raw.get("errorMessage") or raw.get("error") or raw.get("message")
    if status in {"error", "failed", "failure"} or error:
        raise MipBackendError(f"Experiment failed: status={response.get('status')!r}; details={error or raw!r}")
