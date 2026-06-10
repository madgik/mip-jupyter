"""Serializable analysis context — no HTTP calls."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from typing import TYPE_CHECKING
from typing import Sequence

if TYPE_CHECKING:
    from .filters import FilterGroup
    from .transformations import Transformation


@dataclass(frozen=True)
class Context:
    """Describes what is being analyzed."""

    data_model: str
    datasets: tuple[str, ...]
    mip_version: str = "dev"
    filters: FilterGroup | None = None
    transformations: tuple[Transformation, ...] = ()

    def __init__(
        self,
        data_model: str,
        datasets: Sequence[str],
        mip_version: str = "dev",
        filters: FilterGroup | None = None,
        transformations: Sequence[Transformation] = (),
    ):
        if not isinstance(data_model, str) or not data_model.strip():
            raise ValueError("data_model must be a non-empty string.")
        dataset_list = [str(item).strip() for item in (datasets or []) if str(item).strip()]
        if not dataset_list:
            raise ValueError("datasets must contain at least one dataset name.")
        object.__setattr__(self, "data_model", data_model.strip())
        object.__setattr__(self, "datasets", tuple(dataset_list))
        object.__setattr__(self, "mip_version", mip_version or "dev")
        object.__setattr__(self, "filters", filters)
        object.__setattr__(self, "transformations", tuple(transformations or ()))

    def with_transformations(self, transformations: Sequence[Transformation]) -> Context:
        """Return a new context with additional experiment-scoped transformations."""
        return replace(self, transformations=tuple(transformations or ()))

    def with_filters(self, filters: FilterGroup | None) -> Context:
        """Return a new context with replaced top-level filters."""
        return replace(self, filters=filters)
