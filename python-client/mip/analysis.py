"""Analysis set selection and simple exploration helpers."""

from __future__ import annotations

from typing import Any
from typing import Sequence

from .exceptions import MipConfigurationError
from .request_builder import build_inputdata
from .request_builder import code as _code
from .results import Result


class AnalysisSet:
    """Selected data model, datasets, and variables for analysis."""

    def __init__(self, *, data_model: Any, datasets: Sequence[Any], variables: Sequence[Any]):
        self.data_model = data_model
        self.datasets = list(datasets or [])
        self.variables = list(variables or [])
        self._transport = getattr(data_model, "_transport", None)

    def data_model_name(self) -> str:
        return _data_model_name(self.data_model)

    def inputdata(self, *, filters=None, extra_variables: Sequence[Any] | None = None) -> dict:
        variables = [_code(variable) for variable in self.variables]
        if extra_variables:
            seen = set(variables)
            for variable in extra_variables:
                item = _code(variable)
                if item and item not in seen:
                    seen.add(item)
                    variables.append(item)
        return build_inputdata(
            data_model_name=self.data_model_name(),
            datasets=self.datasets,
            variables=variables,
            filters=filters,
        )

    def histogram(self, variable: Any, bins: int | None = None, mode: str = "transient") -> Result:
        from .pipeline import Pipeline

        return Pipeline(analysis_set=self).histogram(variable=variable, bins=bins, mode=mode)

    def summary(self) -> dict[str, Any]:
        return {
            "data_model": self.data_model_name(),
            "datasets": [_code(dataset) for dataset in self.datasets],
            "variables": [_code(variable) for variable in self.variables],
        }

    def explain(self) -> dict[str, Any]:
        return self.inputdata()

    def _repr_html_(self) -> str:
        from .display import render_object_card

        summary = self.summary()
        return render_object_card(
            "AnalysisSet",
            {
                "data_model": summary["data_model"],
                "datasets": ", ".join(summary["datasets"]),
                "variables": ", ".join(summary["variables"]),
            },
            [".summary()", ".explain()", ".help()"],
        )

    def help(self) -> str:
        from .display import show_help

        return show_help("AnalysisSet")

    def _require_transport(self):
        if self._transport is None:
            raise MipConfigurationError(
                "This AnalysisSet is not attached to a Client-created DataModel and cannot execute algorithms."
            )
        return self._transport


def _data_model_name(data_model: Any) -> str:
    code = getattr(data_model, "code", None)
    version = getattr(data_model, "version", None)
    if code and version:
        return f"{code}:{version}"
    return _code(data_model)
