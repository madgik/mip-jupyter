"""Preprocessing step builders for experiment payloads."""

from __future__ import annotations

from typing import Any
from typing import Mapping

from .derived import DerivedVariable
from .labels import internal_code
from .labels import public_label
from .labels import sanitize_mapping_keys


def _serialize_mapping(values: Mapping[Any, Any] | None) -> dict[str, Any]:
    if not values:
        return {}
    return {internal_code(key): value for key, value in values.items()}


class PreprocessingStep:
    name: str = ""

    def __init__(self, **parameters: Any):
        self._parameters = {key: value for key, value in parameters.items() if value not in ({}, None)}

    def spec(self, client=None) -> dict[str, Any]:
        return {"name": self.name, "parameters": dict(self._parameters)}

    def summary(self) -> dict[str, Any]:
        return self.user_summary()

    def user_summary(self) -> dict[str, Any]:
        return {"name": self.name}


class MissingValuesHandler(PreprocessingStep):
    name = "missing_values_handler"

    def __init__(self, *, strategies: Mapping[Any, str], fill_values: Mapping[Any, Any] | None = None):
        self._strategies = dict(strategies or {})
        self._fill_values = dict(fill_values or {})
        parameters = {"strategies": _serialize_mapping(self._strategies)}
        serialized_fill_values = _serialize_mapping(self._fill_values)
        if serialized_fill_values:
            parameters["fill_values"] = serialized_fill_values
        super().__init__(**parameters)

    def user_summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "strategies": {public_label(key): value for key, value in self._strategies.items()},
            "fill_values": {public_label(key): value for key, value in self._fill_values.items()},
        }


class OutlierWinsorizer(PreprocessingStep):
    name = "outlier_winsorizer"

    def __init__(
        self,
        *,
        strategies: Mapping[Any, str],
        tails: Mapping[Any, str] | None = None,
        folds: Mapping[Any, float] | None = None,
    ):
        self._strategies = dict(strategies or {})
        self._tails = dict(tails or {})
        self._folds = dict(folds or {})
        parameters = {"strategies": _serialize_mapping(self._strategies)}
        serialized_tails = _serialize_mapping(self._tails)
        serialized_folds = _serialize_mapping(self._folds)
        if serialized_tails:
            parameters["tails"] = serialized_tails
        if serialized_folds:
            parameters["folds"] = serialized_folds
        super().__init__(**parameters)

    def user_summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "strategies": {public_label(key): value for key, value in self._strategies.items()},
            "tails": {public_label(key): value for key, value in self._tails.items()},
            "folds": {public_label(key): value for key, value in self._folds.items()},
        }


class CategoricalColumnCreator(PreprocessingStep):
    name = "categorical_column_creator"

    def __init__(
        self,
        *,
        label: str,
        rules: dict[str, Any],
        default_enumeration: str | None = None,
    ):
        self.label = label
        self.rules = rules
        self.default_enumeration = default_enumeration
        self._code = DerivedVariable(label=label)._code

        enumerations = list(rules.keys())
        if default_enumeration is not None:
            enumerations.append(default_enumeration)

        self.variable = DerivedVariable(
            label=self.label,
            enumerations=enumerations,
            created_by=self.name,
            _code=self._code,
        )
        self._parameters = self._build_parameters()

    @property
    def enumerations(self) -> list[str]:
        return self.variable.categories()

    def _build_parameters(self) -> dict[str, Any]:
        parameters: dict[str, Any] = {
            "code": self._code,
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

    def user_summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "categories": self.enumerations,
            "default_category": self.default_enumeration,
        }
