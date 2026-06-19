"""Data-model objects built from backend DTOs."""

from __future__ import annotations

from typing import Any
from typing import Mapping

from .datasets import DatasetCollection
from .variables import VariableCollection


class DataModel:
    """Backend data-model metadata with variable and dataset collections."""

    def __init__(self, data: Mapping[str, Any], *, transport=None):
        self._transport = transport
        self._data = dict(data or {})
        self.code = self._data.get("code")
        self.version = self._data.get("version")
        self.label = self._data.get("label") or self.code
        self.longitudinal = self._data.get("longitudinal")
        self.groups = list(self._data.get("groups") or [])
        self.datasets_variables = dict(
            self._data.get("datasetsVariables") or self._data.get("datasets_variables") or {}
        )
        self.variables = VariableCollection(
            _flatten_variables(self._data),
            groups=self.groups,
            root_variables=self.root_variables(),
        )
        self.datasets = DatasetCollection(self._data.get("datasets") or [], data_model=self)

    def __repr__(self) -> str:
        return f"<DataModel(code={self.code!r}, version={self.version!r})>"

    @property
    def name(self) -> str:
        if self.code and self.version:
            return f"{self.code}:{self.version}"
        return str(self.code or self.version or "")

    def metadata(self) -> dict[str, Any]:
        return dict(self._data)

    def summary(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "version": self.version,
            "label": self.label,
            "longitudinal": self.longitudinal,
            "n_variables": len(self.variables),
            "n_datasets": len(self.datasets),
        }

    def root_variables(self) -> list[dict[str, Any]]:
        return [dict(item) for item in (self._data.get("variables") or []) if isinstance(item, Mapping)]

    def list_datasets(self) -> list[dict[str, Any]]:
        return [dataset.summary() for dataset in self.datasets.to_list()]

    def list_variables(self) -> list[dict[str, Any]]:
        return [variable.summary() for variable in self.variables.to_list()]

    def list_groups(self) -> list[dict[str, Any]]:
        from .metadata_tree import list_groups

        return list_groups(self.groups)

    def tree(self, *, group: Any | None = None, include_variables: bool = False, max_lines: int = 250):
        from .metadata_tree import MetadataTree
        from .metadata_tree import find_group
        from .metadata_tree import list_groups
        from .metadata_tree import pathology_from_data_model
        from .metadata_tree import render_pathology_tree

        focus_group = None
        focus_group_path = None
        if group is not None:
            match = find_group(self.groups, group)
            if match is None:
                available = ", ".join(
                    sorted(
                        {
                            str(item.get("code") or item.get("label"))
                            for item in list_groups(self.groups)
                            if item.get("code") or item.get("label")
                        }
                    )
                )
                raise LookupError(f"Unknown group {group!r}. Available groups: {available}")
            focus_group, focus_group_path = match

        pathology = pathology_from_data_model(self)
        return MetadataTree(
            render_pathology_tree(
                pathology,
                include_variables=include_variables,
                max_lines=max_lines,
                focus_group=focus_group,
                focus_group_path=focus_group_path,
            )
        )


def _flatten_variables(data: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    items: list[Mapping[str, Any]] = []
    seen: set[str] = set()

    def add(variable: Any) -> None:
        if not isinstance(variable, Mapping):
            return
        code = variable.get("code")
        if code is None or code in seen:
            return
        seen.add(code)
        items.append(variable)

    def visit_group(group: Any) -> None:
        if not isinstance(group, Mapping):
            return
        for variable in group.get("variables") or []:
            add(variable)
        for child in group.get("groups") or []:
            visit_group(child)

    for variable in data.get("variables") or []:
        add(variable)
    for group in data.get("groups") or []:
        visit_group(group)
    return items
