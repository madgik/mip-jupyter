"""Dataset wrappers for backend data-model metadata."""

from __future__ import annotations

from typing import Any
from typing import Iterable
from typing import Mapping

from .variables import Variable
from .variables import VariableCollection


def _variable_code(variable: Any) -> str:
    return str(getattr(variable, "code", variable))


class Dataset:
    """One dataset entry from a backend data model."""

    def __init__(self, data: Mapping[str, Any], *, data_model: Any | None = None):
        self._data = dict(data or {})
        self._data_model = data_model
        self.code = self._data.get("code")
        self.label = self._data.get("label") or self.code

    def __repr__(self) -> str:
        return f"<Dataset(code={self.code!r})>"

    def _repr_html_(self) -> str:
        from .display import render_object_card

        return render_object_card(
            f"Dataset: {self.code}",
            {
                "code": self.code,
                "label": self.label,
                "n_variables": len(self.variables()),
            },
            [".summary()", ".metadata()", ".variables()", ".help()"],
        )

    def help(self) -> str:
        from .display import show_help

        return show_help("Dataset")

    def metadata(self) -> dict[str, Any]:
        return dict(self._data)

    def variables(self) -> list[Variable]:
        if self._data_model is None:
            return []
        allowed = set((self._data_model.datasets_variables or {}).get(self.code, []) or [])
        if not allowed:
            return self._data_model.variables.to_list()
        return [variable for variable in self._data_model.variables if variable.code in allowed]

    def has_variable(self, variable: Variable | str) -> bool:
        code = _variable_code(variable)
        return any(item.code == code for item in self.variables())

    def summary(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "label": self.label,
            "n_variables": len(self.variables()),
        }


class DatasetCollection:
    """Indexable collection of datasets for a data model."""

    def __init__(self, datasets: Iterable[Dataset | Mapping[str, Any]], *, data_model: Any | None = None):
        self._items = [
            item if isinstance(item, Dataset) else Dataset(item, data_model=data_model)
            for item in datasets
        ]
        self._by_code = {item.code: item for item in self._items if item.code is not None}

    def __iter__(self):
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, code: str) -> Dataset:
        try:
            return self._by_code[code]
        except KeyError as exc:
            raise KeyError(f"Unknown dataset: {code}") from exc

    def search(self, text: str = "") -> list[Dataset]:
        needle = str(text or "").lower()
        if not needle:
            return self.to_list()
        return [
            item
            for item in self._items
            if needle in str(item.code or "").lower() or needle in str(item.label or "").lower()
        ]

    def to_list(self) -> list[Dataset]:
        return list(self._items)

    def list(self) -> list[Dataset]:
        """Return all datasets as a list."""
        return self.to_list()

    def to_frame(self):
        from .display import to_frame

        return to_frame(self._items)

    def help(self) -> str:
        from .display import show_help

        return show_help("DatasetCollection")
