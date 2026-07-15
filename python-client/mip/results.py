"""Raw-first result wrappers with notebook-friendly previews."""

from __future__ import annotations

from typing import Any

from .display import HelpText
from .display import histogram_bins_counts
from .display import render_result_card
from .display import result_highlights
from .display import result_table_rows
from .display import show_help
from .display import to_frame
from .exceptions import UnsupportedOperationError
from .sklearn import feature_schema_from_logistic_result
from .sklearn import logistic_regression_to_sklearn


class Result:
    """Backend result wrapper with minimal notebook helpers."""

    def __init__(self, *, raw: Any, payload: Any = None, result_type: str | None = None):
        self.raw = raw
        self.payload = payload if payload is not None else raw
        self.result_type = result_type

    def summary(self) -> Any:
        return self.raw

    def highlights(self) -> dict[str, Any]:
        """Return compact key metrics for this result type."""
        return result_highlights(self.result_type, self.raw)

    def to_frame(self):
        """Return a tabular preview of the primary result table when available."""
        rows = result_table_rows(self.result_type, self.raw)
        if not rows:
            raise UnsupportedOperationError(
                f"No tabular preview is available for result type {self.result_type!r}. "
                "Use .summary() or .raw for the backend payload."
            )
        return to_frame(rows)

    def _repr_html_(self) -> str:
        methods = [".highlights()", ".to_frame()", ".summary()", ".raw", ".payload", ".help()"]
        if self.result_type == "histogram":
            methods.insert(2, ".plot()")
        return render_result_card(result_type=self.result_type, raw=self.raw, methods=methods)

    def help(self) -> HelpText:
        return show_help("Result")

    def plot(self):
        if self.result_type != "histogram":
            raise UnsupportedOperationError(f"Plotting is not supported for result type {self.result_type!r}.")
        data = _histogram_data(self.raw)
        if data is None:
            raise UnsupportedOperationError("This histogram result does not contain plottable bins/counts data.")
        try:
            import matplotlib.pyplot as plt
        except Exception as exc:
            raise UnsupportedOperationError("Histogram plotting requires matplotlib to be installed.") from exc
        bins, counts = data
        variable = _histogram_variable(self.raw)
        _figure, axis = plt.subplots()
        axis.bar(range(len(counts)), counts, tick_label=[str(item) for item in bins])
        axis.set_ylabel("count")
        axis.set_xlabel(variable or "bin")
        axis.set_title(f"Histogram{f': {variable}' if variable else ''}")
        if len(bins) > 8:
            axis.tick_params(axis="x", labelrotation=45)
        _figure.tight_layout()
        return axis


class ModelResult(Result):
    """Model result with logistic-regression sklearn export support."""

    def __init__(
        self,
        *,
        raw: Any,
        payload: Any = None,
        result_type: str | None = None,
        positive_class: Any = None,
    ):
        super().__init__(raw=raw, payload=payload, result_type=result_type)
        self.positive_class = positive_class

    def feature_schema(self) -> dict[str, Any]:
        return feature_schema_from_logistic_result(self.raw)

    def to_sklearn(self):
        if self.result_type != "logistic_regression":
            raise UnsupportedOperationError("Only logistic regression results can be exported to sklearn.")
        return logistic_regression_to_sklearn(self.raw, positive_class=self.positive_class)

    def _repr_html_(self) -> str:
        methods = [
            ".highlights()",
            ".to_frame()",
            ".summary()",
            ".feature_schema()",
            ".to_sklearn()",
            ".help()",
        ]
        return render_result_card(result_type=self.result_type, raw=self.raw, methods=methods)

    def help(self) -> HelpText:
        return show_help("ModelResult")


def _histogram_data(raw: Any):
    payload = raw if isinstance(raw, dict) else {}
    bins, counts = histogram_bins_counts(payload)
    if not bins or not counts:
        return None
    return bins, counts


def _histogram_variable(raw: Any) -> str | None:
    payload = raw if isinstance(raw, dict) else {}
    for key in ("variable", "var", "label"):
        value = payload.get(key)
        if value:
            return str(value)
    histogram = payload.get("histogram")
    if isinstance(histogram, dict):
        for key in ("variable", "var", "label"):
            value = histogram.get(key)
            if value:
                return str(value)
    if isinstance(histogram, list) and histogram and isinstance(histogram[0], dict):
        for key in ("variable", "var", "label"):
            value = histogram[0].get(key)
            if value:
                return str(value)
    return None
