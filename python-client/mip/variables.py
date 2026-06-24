"""Variable wrappers for backend data-model metadata."""

from __future__ import annotations

from typing import Any
from typing import Iterable
from typing import Mapping

from .display import HelpText
from .labels import enumeration_code_for_label
from .labels import enumeration_labels
from .labels import lookup_by_label
from .labels import normalize_label


class Variable:
    """One backend data-model variable."""

    def __init__(self, data: Mapping[str, Any]):
        self._data = dict(data or {})
        self._code = self._data.get("code")
        self.label = self._data.get("label") or self._code

    def __repr__(self) -> str:
        return f"<Variable(label={self.label!r})>"

    def _repr_html_(self) -> str:
        from .display import render_object_card

        return render_object_card(
            f"Variable: {self.label}",
            {
                "label": self.label,
                "type": self._data.get("type"),
                "numerical": self.is_numerical(),
                "categorical": self.is_categorical(),
            },
            [".summary()", ".details()", ".categories()", ".help()"],
        )

    def help(self) -> HelpText:
        from .display import show_help

        return show_help("Variable")

    def details(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "type": self._data.get("type"),
            "categorical": self.is_categorical(),
            "numerical": self.is_numerical(),
            "categories": self.categories(),
        }

    def is_numerical(self) -> bool:
        kind = str(self._data.get("type") or self._data.get("sql_type") or "").lower()
        categorical = str(self._data.get("is_categorical") or "").lower()
        return categorical not in {"true", "1", "yes"} and kind in {
            "real",
            "integer",
            "int",
            "float",
            "double",
            "numeric",
            "number",
        }

    def is_categorical(self) -> bool:
        categorical = str(self._data.get("is_categorical") or "").lower()
        if categorical in {"true", "1", "yes"}:
            return True
        kind = str(self._data.get("type") or "").lower()
        return kind in {"nominal", "categorical", "ordinal", "text", "string", "boolean", "bool"}

    def categories(self) -> list[str]:
        raw = self._data.get("enumerations") or self._data.get("enums") or []
        return enumeration_labels(raw)

    def enumeration_code_for(self, value: Any) -> str | None:
        raw = self._data.get("enumerations") or self._data.get("enums") or []
        return enumeration_code_for_label(raw, value)

    def summary(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "type": self._data.get("type"),
            "categorical": self.is_categorical(),
            "numerical": self.is_numerical(),
        }


class VariableCollection:
    """Indexable collection of variables for a data model."""

    def __init__(
        self,
        variables: Iterable[Variable | Mapping[str, Any]],
        *,
        groups: Iterable[Any] | None = None,
        root_variables: Iterable[Mapping[str, Any]] | None = None,
    ):
        self._items = [item if isinstance(item, Variable) else Variable(item) for item in variables]
        self._by_code = {item._code: item for item in self._items if item._code is not None}
        self._groups = list(groups or [])
        self._root_variables = [dict(item) for item in (root_variables or []) if isinstance(item, Mapping)]

    def __iter__(self):
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, label: str) -> Variable:
        return lookup_by_label(self._items, label, kind="variable")

    def search(self, text: str = "") -> list[Variable]:
        needle = normalize_label(text)
        if not needle:
            return self.to_list()

        def description(item: Variable) -> str:
            return str(item._data.get("desc") or item._data.get("description") or "")

        return [
            item
            for item in self._items
            if needle in normalize_label(item.label) or needle in normalize_label(description(item))
        ]

    def numerical(self) -> list[Variable]:
        return [item for item in self._items if item.is_numerical()]

    def categorical(self) -> list[Variable]:
        return [item for item in self._items if item.is_categorical()]

    def to_list(self) -> list[Variable]:
        return list(self._items)

    def list(self) -> list[Variable]:
        """Return all variables as a flat list."""
        return self.to_list()

    def tree(self, *, group: Any | None = None, max_lines: int = 250):
        """Render variables in their backend group hierarchy."""
        from .metadata_tree import MetadataTree
        from .metadata_tree import find_group
        from .metadata_tree import list_groups
        from .metadata_tree import PathologyView
        from .metadata_tree import render_pathology_tree

        focus_group = None
        focus_group_path = None
        if group is not None:
            match = find_group(self._groups, group)
            if match is None:
                available = ", ".join(
                    sorted(
                        {
                            str(item.get("label") or item.get("path", [""])[-1])
                            for item in list_groups(self._groups)
                            if item.get("label") or item.get("path")
                        }
                    )
                )
                raise LookupError(f"Unknown group {group!r}. Available groups: {available}")
            focus_group, focus_group_path = match

        pathology = PathologyView(
            code=None,
            version=None,
            label="Variables",
            longitudinal=None,
            variables=self._root_variables,
            groups=self._groups,
            datasets=[],
            datasets_variables={},
        )
        return MetadataTree(
            render_pathology_tree(
                pathology,
                include_variables=True,
                max_lines=max_lines,
                focus_group=focus_group,
                focus_group_path=focus_group_path,
            )
        )

    def to_frame(self):
        from .display import to_frame

        return to_frame(self._items)

    def help(self) -> HelpText:
        from .display import show_help

        return show_help("VariableCollection")
