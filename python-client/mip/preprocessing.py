"""Preprocessing step builders for experiment payloads."""

from __future__ import annotations

from typing import Any
from typing import Mapping

from .derived import DerivedVariable


def _code(value: Any) -> str:
    return str(getattr(value, "code", value))


def _serialize_mapping(values: Mapping[Any, Any] | None) -> dict[str, Any]:
    if not values:
        return {}
    return {_code(key): value for key, value in values.items()}


class PreprocessingStep:
    name: str = ""

    def __init__(self, **parameters: Any):
        self._parameters = {key: value for key, value in parameters.items() if value not in ({}, None)}

    def spec(self, client=None) -> dict[str, Any]:
        return {"name": self.name, "parameters": dict(self._parameters)}

    def summary(self) -> dict[str, Any]:
        return self.spec()


class MissingValuesHandler(PreprocessingStep):
    name = "missing_values_handler"

    def __init__(self, *, strategies: Mapping[Any, str], fill_values: Mapping[Any, Any] | None = None):
        parameters = {"strategies": _serialize_mapping(strategies)}
        serialized_fill_values = _serialize_mapping(fill_values)
        if serialized_fill_values:
            parameters["fill_values"] = serialized_fill_values
        super().__init__(**parameters)


class OutlierWinsorizer(PreprocessingStep):
    name = "outlier_winsorizer"

    def __init__(
        self,
        *,
        strategies: Mapping[Any, str],
        tails: Mapping[Any, str] | None = None,
        folds: Mapping[Any, float] | None = None,
    ):
        parameters = {"strategies": _serialize_mapping(strategies)}
        serialized_tails = _serialize_mapping(tails)
        serialized_folds = _serialize_mapping(folds)
        if serialized_tails:
            parameters["tails"] = serialized_tails
        if serialized_folds:
            parameters["folds"] = serialized_folds
        super().__init__(**parameters)


class CategoricalColumnCreator(PreprocessingStep):
    name = "categorical_column_creator"

    def __init__(
        self,
        code: str,
        rules: dict[str, Any],
        default_enumeration: str | None = None,
        label: str | None = None,
    ):
        self.code = code
        self.rules = rules
        self.default_enumeration = default_enumeration
        self.label = label or code

        enumerations = list(rules.keys())
        if default_enumeration is not None:
            enumerations.append(default_enumeration)

        self.variable = DerivedVariable(
            code=code,
            label=self.label,
            enumerations=enumerations,
            created_by=self.name,
        )
        self._parameters = self._build_parameters()

    @property
    def enumerations(self) -> list[str]:
        return self.variable.categories()

    def _build_parameters(self) -> dict[str, Any]:
        parameters: dict[str, Any] = {
            "code": self.code,
            "strategy": "filter_rules",
            "rules": {
                enumeration: rule.to_payload() if hasattr(rule, "to_payload") else rule.explain()
                for enumeration, rule in self.rules.items()
            },
        }
        if self.default_enumeration is not None:
            parameters["default_enumeration"] = self.default_enumeration
        return parameters

    def spec(self, client=None) -> dict[str, Any]:
        return {"name": self.name, "parameters": dict(self._parameters)}

    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "code": self.code,
            "enumerations": self.enumerations,
            "default_enumeration": self.default_enumeration,
        }
