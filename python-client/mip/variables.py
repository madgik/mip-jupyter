"""Variable wrappers for backend data-model metadata."""

from __future__ import annotations

from typing import Any
from typing import Iterable
from typing import Mapping


class Variable:
    """One backend data-model variable."""

    def __init__(self, data: Mapping[str, Any]):
        self._data = dict(data or {})
        self.code = self._data.get("code")
        self.label = self._data.get("label") or self.code

    def __repr__(self) -> str:
        return f"<Variable(code={self.code!r})>"

    def _repr_html_(self) -> str:
        from .display import render_object_card

        return render_object_card(
            f"Variable: {self.code}",
            {
                "label": self.label,
                "type": self._data.get("type"),
                "numerical": self.is_numerical(),
                "categorical": self.is_categorical(),
            },
            [".summary()", ".metadata()", ".categories()", ".help()"],
        )

    def help(self) -> str:
        from .display import show_help

        return show_help("Variable")

    def metadata(self) -> dict[str, Any]:
        return dict(self._data)

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

    def categories(self) -> list[Any]:
        values = self._data.get("enumerations") or self._data.get("enums") or []
        if isinstance(values, Mapping):
            return list(values.keys())
        if isinstance(values, (list, tuple)):
            return list(values)
        return []

    def summary(self) -> dict[str, Any]:
        return {
            "code": self.code,
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
        self._by_code = {item.code: item for item in self._items if item.code is not None}
        self._groups = list(groups or [])
        self._root_variables = [dict(item) for item in (root_variables or []) if isinstance(item, Mapping)]

    def __iter__(self):
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, code: str) -> Variable:
        try:
            return self._by_code[code]
        except KeyError as exc:
            raise KeyError(f"Unknown variable: {code}") from exc

    def search(self, text: str = "") -> list[Variable]:
        needle = str(text or "").lower()
        if not needle:
            return self.to_list()
        return [
            item
            for item in self._items
            if needle in str(item.code or "").lower() or needle in str(item.label or "").lower()
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
                            str(item.get("code") or item.get("label"))
                            for item in list_groups(self._groups)
                            if item.get("code") or item.get("label")
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

    def help(self) -> str:
        from .display import show_help

        return show_help("VariableCollection")
