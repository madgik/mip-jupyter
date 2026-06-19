"""Raw-first result wrappers."""

from __future__ import annotations

from typing import Any

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
        _figure, axis = plt.subplots()
        axis.bar(bins, counts)
        axis.set_ylabel("count")
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


def _histogram_data(raw: Any):
    payload = raw if isinstance(raw, dict) else {}
    bins = payload.get("bins") or payload.get("x")
    counts = payload.get("counts") or payload.get("y")
    histogram = payload.get("histogram")
    if bins is None and isinstance(histogram, dict):
        bins = histogram.get("bins")
        counts = histogram.get("counts")
    if bins is None and isinstance(histogram, list) and histogram:
        first = histogram[0]
        if isinstance(first, dict):
            bins = first.get("bins")
            counts = first.get("counts")
    if not bins or not counts:
        return None
    return list(bins), list(counts)
