"""Experiment-scoped variable transformations."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any
from typing import List
from typing import Sequence

from .filters import MISSING
from .filters import Case
from .filters import Validation


class Transformation(ABC):
    """Base class for experiment-scoped transformations."""

    scope: str = "experiment"

    @abstractmethod
    def to_preprocessing_dict(self) -> dict:
        """Serialize into preprocessing payload fragment."""


@dataclass(frozen=True)
class CategoricalFromFilters(Transformation):
    """Derive a nominal variable from labeled filter cases."""

    name: str
    label: str
    cases: tuple[Case, ...]
    otherwise: Any = MISSING
    validation: Validation | None = None
    scope: str = "experiment"

    def __init__(
        self,
        name: str,
        label: str,
        cases: Sequence[Case],
        otherwise: Any = MISSING,
        validation: Validation | None = None,
        scope: str = "experiment",
    ):
        if not name or not str(name).strip():
            raise ValueError("name must be a non-empty string.")
        if not cases:
            raise ValueError("cases must contain at least one Case.")
        object.__setattr__(self, "name", str(name).strip())
        object.__setattr__(self, "label", label or name)
        object.__setattr__(self, "cases", tuple(cases))
        object.__setattr__(self, "otherwise", otherwise)
        object.__setattr__(self, "validation", validation)
        object.__setattr__(self, "scope", scope or "experiment")

    def to_preprocessing_dict(self) -> dict:
        otherwise_value = None if self.otherwise is MISSING else self.otherwise
        payload: dict = {
            "name": self.name,
            "label": self.label,
            "cases": [case.to_dict() for case in self.cases],
            "otherwise": otherwise_value,
        }
        if self.validation is not None:
            payload["validation"] = self.validation.to_dict()
        return payload


class TransformationsNamespace:
    """Namespace for creating transformations from an Analysis instance."""

    def __init__(self, analysis: Any):
        self._analysis = analysis

    def categorical_from_filters(
        self,
        name: str,
        label: str,
        cases: Sequence[Case],
        otherwise: Any = MISSING,
        validation: Validation | None = None,
        scope: str = "experiment",
    ) -> CategoricalFromFilters:
        return CategoricalFromFilters(
            name=name,
            label=label,
            cases=cases,
            otherwise=otherwise,
            validation=validation,
            scope=scope,
        )


def serialize_transformations(transformations: Sequence[Transformation]) -> dict:
    """Build categorical_from_filters preprocessing block from context transformations."""
    variables: List[dict] = []
    for transformation in transformations or ():
        if isinstance(transformation, CategoricalFromFilters):
            variables.append(transformation.to_preprocessing_dict())
    if not variables:
        return {}
    return {"categorical_from_filters": {"variables": variables}}
