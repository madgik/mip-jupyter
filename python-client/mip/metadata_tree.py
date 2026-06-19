"""ASCII metadata tree rendering for catalog discovery in notebooks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Iterable
from typing import Mapping

from .datamodel import DataModel


class MetadataTree(str):
    """String wrapper with notebook-friendly repr and display."""

    def __repr__(self) -> str:
        return str(self)

    def _repr_html_(self) -> str:
        escaped = (
            str(self)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        return f"<pre>{escaped}</pre>"

    def display(self) -> None:
        try:
            from IPython.display import display
        except ImportError:
            print(self)
            return
        display(self)


@dataclass(frozen=True)
class PathologyView:
    """Notebook-friendly view of a backend data model."""

    code: str | None
    version: str | None
    label: str | None
    longitudinal: bool | None
    variables: list[Any]
    groups: list[Any]
    datasets: list[Any]
    datasets_variables: Mapping[str, list[Any]]

    @property
    def name(self) -> str:
        if self.code and self.version:
            return f"{self.code}:{self.version}"
        return str(self.code or self.version or "")


def pathology_from_data_model(model: DataModel) -> PathologyView:
    return PathologyView(
        code=model.code,
        version=model.version,
        label=model.label,
        longitudinal=model.longitudinal,
        variables=list(model.root_variables()),
        groups=list(model.groups or []),
        datasets=[dataset.metadata() for dataset in model.datasets.to_list()],
        datasets_variables=dict(model.datasets_variables or {}),
    )


def render_catalog_tree(models: list[DataModel], *, max_lines: int = 250) -> str:
    writer = _LineWriter(max_lines=max_lines)
    writer.add(f"Data models ({len(models)})")
    if not models:
        return writer.render()

    ordered = sorted(
        [pathology_from_data_model(model) for model in models],
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
        writer.add(
            f"{connector} {_format_name_label(model.code, model.label)}:{model.version} "
            f"[{', '.join(summary)}]"
        )
    return writer.render()


def render_pathology_tree(
    pathology: PathologyView,
    *,
    include_variables: bool = False,
    max_lines: int = 250,
    focus_group: Any | None = None,
    focus_group_path: list[str] | None = None,
) -> str:
    if focus_group is not None:
        return render_group_subtree(
            focus_group,
            model_name=pathology.name,
            model_label=pathology.label,
            group_path=focus_group_path,
            include_variables=include_variables,
            max_lines=max_lines,
        )

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


def render_group_subtree(
    group: Any,
    *,
    model_name: str | None = None,
    model_label: str | None = None,
    group_path: list[str] | None = None,
    include_variables: bool = True,
    max_lines: int = 250,
) -> str:
    writer = _LineWriter(max_lines=max_lines)
    path_parts = [str(part) for part in (group_path or []) if part]
    if not path_parts:
        path_parts = [_format_name_label(_item_get(group, "code"), _item_get(group, "label"))]
    path_text = " > ".join(path_parts)
    if model_name:
        title = f"Metadata tree for {model_name}"
        if model_label and model_label != model_name:
            title += f" ({model_label})"
        title += f" > {path_text}"
    else:
        title = f"Variables > {path_text}"
    writer.add(title)
    _render_group(
        writer=writer,
        group=group,
        prefix="",
        is_last=True,
        include_variables=include_variables,
    )
    return writer.render()


def find_group(groups: Iterable[Any], selector: Any) -> tuple[Any, list[str]] | None:
    needle = _group_selector(selector)
    if not needle:
        return None

    def visit(group: Any, path: list[str]) -> tuple[Any, list[str]] | None:
        code = str(_item_get(group, "code") or "").strip()
        label = str(_item_get(group, "label") or "").strip()
        current_path = path + [code or label or "<unknown>"]
        if _matches_group_selector(group, needle):
            return group, current_path
        for child in _item_get(group, "groups", default=[]):
            found = visit(child, current_path)
            if found is not None:
                return found
        return None

    for group in _as_list(groups):
        found = visit(group, [])
        if found is not None:
            return found
    return None


def list_groups(groups: Iterable[Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    def visit(group: Any, path: list[str]) -> None:
        code = str(_item_get(group, "code") or "").strip()
        label = str(_item_get(group, "label") or "").strip()
        current_path = path + [code or label or "<unknown>"]
        items.append({"code": code or None, "label": label or None, "path": current_path})
        for child in _item_get(group, "groups", default=[]):
            visit(child, current_path)

    for group in _as_list(groups):
        visit(group, [])
    return items


def _group_selector(selector: Any) -> str:
    if isinstance(selector, Mapping):
        return str(selector.get("code") or selector.get("label") or "").strip().lower()
    return str(selector or "").strip().lower()


def _matches_group_selector(group: Any, needle: str) -> bool:
    code = str(_item_get(group, "code") or "").strip().lower()
    label = str(_item_get(group, "label") or "").strip().lower()
    return needle in {code, label}


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
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
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
    code = str(_item_get(dataset, "code") or "").strip()
    if label and code and label != code:
        return f"{label} ({code})"
    if label:
        return label
    if code:
        return code
    return "<unknown>"


def _format_variable(variable: Any) -> str:
    code = _item_get(variable, "code")
    label = _item_get(variable, "label")
    variable_type = _item_get(variable, "type")
    text = _format_name_label(code, label)
    if variable_type:
        text += f" [{variable_type}]"
    return text
