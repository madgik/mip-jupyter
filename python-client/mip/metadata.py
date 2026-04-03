"""Metadata/pathology helpers for notebook users."""

from __future__ import annotations

import builtins
from dataclasses import dataclass
from typing import Any, Iterable, List, Mapping, Optional

from .data_model import DataModel


class MetadataTree(str):
    """String wrapper with notebook-friendly repr for tree descriptions."""

    def __repr__(self) -> str:  # pragma: no cover - tiny display helper
        return str(self)


@dataclass(frozen=True)
class Pathology:
    """Notebook-friendly view of a backend data model."""

    code: Optional[str]
    version: Optional[str]
    label: Optional[str]
    longitudinal: Optional[bool]
    variables: list
    groups: list
    datasets: list
    datasets_variables: Mapping[str, list]

    @property
    def name(self) -> str:
        code = self.code or ""
        version = self.version or ""
        if code and version:
            return f"{code}:{version}"
        return code or version


def _to_pathology(model: DataModel) -> Pathology:
    return Pathology(
        code=model.code,
        version=model.version,
        label=model.label,
        longitudinal=model.longitudinal,
        variables=builtins.list(model.variables or []),
        groups=builtins.list(model.groups or []),
        datasets=builtins.list(model.datasets or []),
        datasets_variables=dict(model.datasets_variables or {}),
    )


def _iter_models() -> Iterable[DataModel]:
    return DataModel.list()


def list() -> List[Pathology]:  # noqa: A001 - public API follows notebook convention
    """List all available pathologies/data models."""
    return [_to_pathology(model) for model in _iter_models()]


def get_pathology(code_or_code_version: str) -> Pathology:
    """Get pathology metadata by code or `code:version`.

    Args:
        code_or_code_version: Either `dementia` or `dementia:0.1`.

    Raises:
        LookupError: when no matching pathology is found, or the code maps to
            multiple versions and no explicit version is provided.
    """
    if not isinstance(code_or_code_version, str) or not code_or_code_version.strip():
        raise ValueError("code_or_code_version must be a non-empty string.")

    selector = code_or_code_version.strip()
    models = builtins.list(_iter_models())
    if ":" in selector:
        code, version = selector.split(":", 1)
        for model in models:
            if model.code == code and str(model.version) == version:
                return _to_pathology(model)
        raise LookupError(f"No pathology found for '{selector}'.")

    matched = [m for m in models if m.code == selector]
    if not matched:
        raise LookupError(f"No pathology found for '{selector}'.")
    if len(matched) > 1:
        available = ", ".join(sorted(f"{m.code}:{m.version}" for m in matched))
        raise LookupError(
            "Multiple pathology versions found. Use '<code>:<version>'. "
            f"Available for '{selector}': {available}"
        )
    return _to_pathology(matched[0])


def describe(
    pathology: Optional[str | Pathology | DataModel] = None,
    *,
    include_variables: bool = False,
    max_lines: int = 250,
):
    """Describe metadata as an ASCII tree.

    Examples:
        metadata.describe()  # all available data models (summary tree)
        metadata.describe("dementia:0.1")  # single model hierarchy
        metadata.describe("dementia:0.1", include_variables=True)
    """
    models = builtins.list(_iter_models())

    if pathology is None:
        return MetadataTree(_describe_catalog(models=models, max_lines=max_lines))

    resolved = _resolve_pathology(pathology=pathology, models=models)
    return MetadataTree(
        _describe_pathology(
            pathology=resolved,
            include_variables=include_variables,
            max_lines=max_lines,
        )
    )


def _resolve_pathology(pathology: str | Pathology | DataModel, models: list[DataModel]) -> Pathology:
    if isinstance(pathology, Pathology):
        return pathology
    if isinstance(pathology, DataModel):
        return _to_pathology(pathology)
    if isinstance(pathology, str):
        selector = pathology.strip()
        if not selector:
            raise ValueError("pathology must be a non-empty string.")
        if ":" in selector:
            code, version = selector.split(":", 1)
            for model in models:
                if model.code == code and str(model.version) == version:
                    return _to_pathology(model)
            raise LookupError(f"No pathology found for '{selector}'.")

        matched = [m for m in models if m.code == selector]
        if not matched:
            raise LookupError(f"No pathology found for '{selector}'.")
        if len(matched) > 1:
            available = ", ".join(sorted(f"{m.code}:{m.version}" for m in matched))
            raise LookupError(
                "Multiple pathology versions found. Use '<code>:<version>'. "
                f"Available for '{selector}': {available}"
            )
        return _to_pathology(matched[0])

    raise TypeError("pathology must be a code string, Pathology, or DataModel.")


class _LineWriter:
    def __init__(self, max_lines: int):
        self.max_lines = max(1, int(max_lines))
        self.lines: list[str] = []
        self.truncated = False

    def add(self, line: str) -> bool:
        if len(self.lines) >= self.max_lines:
            self.truncated = True
            return False
        self.lines.append(line)
        return True

    def render(self) -> str:
        if self.truncated:
            if self.lines:
                self.lines[-1] = "... (truncated)"
            else:
                self.lines.append("... (truncated)")
        return "\n".join(self.lines)


def _describe_catalog(models: list[DataModel], max_lines: int) -> str:
    writer = _LineWriter(max_lines=max_lines)
    writer.add(f"Data models ({len(models)})")
    if not models:
        return writer.render()

    ordered = sorted(
        [_to_pathology(model) for model in models],
        key=lambda model: ((model.code or "").lower(), str(model.version or "").lower()),
    )
    for index, model in enumerate(ordered):
        connector = "`--" if index == len(ordered) - 1 else "|--"
        groups_count = _count_group_nodes(model.groups)
        grouped_variables_count = _count_group_variables(model.groups)
        summary = [
            f"{len(model.datasets)} datasets",
            f"{len(model.variables)} root vars",
            f"{groups_count} groups",
            f"{grouped_variables_count} grouped vars",
        ]
        writer.add(f"{connector} {_format_name_label(model.code, model.label)}:{model.version} [{', '.join(summary)}]")
    return writer.render()


def _describe_pathology(pathology: Pathology, include_variables: bool, max_lines: int) -> str:
    writer = _LineWriter(max_lines=max_lines)
    title = f"Metadata tree for {pathology.name or '<unknown>'}"
    if pathology.label and pathology.label != pathology.name:
        title += f" ({pathology.label})"
    writer.add(title)

    sections: list[tuple[str, Any]] = []
    if pathology.longitudinal is not None:
        sections.append(("longitudinal", pathology.longitudinal))
    sections.append(("datasets", pathology.datasets))
    sections.append(("groups", pathology.groups))
    sections.append(("root_variables", pathology.variables))

    for index, (name, value) in enumerate(sections):
        is_last = index == len(sections) - 1
        connector = "`--" if is_last else "|--"
        prefix = "   " if is_last else "|  "

        if name == "longitudinal":
            writer.add(f"{connector} longitudinal: {bool(value)}")
            continue

        if name == "datasets":
            datasets = _as_list(value)
            writer.add(f"{connector} datasets ({len(datasets)})")
            for dataset_index, dataset in enumerate(datasets):
                dataset_last = dataset_index == len(datasets) - 1
                dataset_connector = "`--" if dataset_last else "|--"
                writer.add(f"{prefix}{dataset_connector} {_format_dataset(dataset)}")
            continue

        if name == "groups":
            groups = _as_list(value)
            writer.add(f"{connector} groups ({len(groups)})")
            for group_index, group in enumerate(groups):
                _render_group(
                    writer=writer,
                    group=group,
                    prefix=prefix,
                    is_last=group_index == len(groups) - 1,
                    include_variables=include_variables,
                )
            continue

        if name == "root_variables":
            variables = _as_list(value)
            writer.add(f"{connector} root_variables ({len(variables)})")
            if include_variables:
                for variable_index, variable in enumerate(variables):
                    variable_last = variable_index == len(variables) - 1
                    variable_connector = "`--" if variable_last else "|--"
                    writer.add(f"{prefix}{variable_connector} {_format_variable(variable)}")
            continue

    return writer.render()


def _render_group(
    writer: _LineWriter,
    group: Any,
    prefix: str,
    is_last: bool,
    include_variables: bool,
) -> None:
    variables = _as_list(_item_get(group, "variables", default=[]))
    subgroups = _as_list(_item_get(group, "groups", default=[]))
    connector = "`--" if is_last else "|--"
    node_name = _format_name_label(_item_get(group, "code"), _item_get(group, "label"))
    summary_parts = [f"{len(variables)} vars"]
    if subgroups:
        summary_parts.append(f"{len(subgroups)} groups")
    writer.add(f"{prefix}{connector} {node_name} [{', '.join(summary_parts)}]")

    child_prefix = prefix + ("   " if is_last else "|  ")
    children: list[tuple[str, Any]] = []
    if include_variables:
        for variable in variables:
            children.append(("variable", variable))
    for subgroup in subgroups:
        children.append(("group", subgroup))

    for child_index, (kind, node) in enumerate(children):
        child_last = child_index == len(children) - 1
        if kind == "variable":
            child_connector = "`--" if child_last else "|--"
            writer.add(f"{child_prefix}{child_connector} {_format_variable(node)}")
            continue

        _render_group(
            writer=writer,
            group=node,
            prefix=child_prefix,
            is_last=child_last,
            include_variables=include_variables,
        )


def _count_group_nodes(groups: Iterable[Any]) -> int:
    total = 0
    for group in _as_list(groups):
        total += 1
        total += _count_group_nodes(_item_get(group, "groups", default=[]))
    return total


def _count_group_variables(groups: Iterable[Any]) -> int:
    total = 0
    for group in _as_list(groups):
        total += len(_as_list(_item_get(group, "variables", default=[])))
        total += _count_group_variables(_item_get(group, "groups", default=[]))
    return total


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, builtins.list):
        return value
    if isinstance(value, tuple):
        return builtins.list(value)
    return [value]


def _item_get(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


def _format_name_label(code: Any, label: Any) -> str:
    label_text = str(label or "").strip()
    if label_text:
        return label_text
    return str(code or "<unknown>")


def _format_dataset(dataset: Any) -> str:
    if isinstance(dataset, str):
        return dataset
    label = str(_item_get(dataset, "label") or "").strip()
    if label:
        return label
    return "<unknown>"


def _format_variable(variable: Any) -> str:
    code = _item_get(variable, "code")
    label = _item_get(variable, "label")
    variable_type = _item_get(variable, "type")
    text = _format_name_label(code, label)
    if variable_type:
        text += f" [{variable_type}]"
    return text
