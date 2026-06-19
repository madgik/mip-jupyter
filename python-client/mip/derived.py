"""Derived variables created by preprocessing steps."""

from __future__ import annotations

from typing import Any


class DerivedVariable:
    """A categorical variable created by preprocessing, not from the catalog."""

    def __init__(
        self,
        code: str,
        label: str | None = None,
        enumerations: list[str] | None = None,
        created_by: str | None = None,
    ):
        self.code = code
        self.label = label or code
        self._enumerations = list(enumerations or [])
        self.created_by = created_by

    def __repr__(self) -> str:
        return f"<DerivedVariable(code={self.code!r})>"

    def metadata(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "label": self.label,
            "sql_type": "text",
            "is_categorical": True,
            "enumerations": {value: value for value in self._enumerations},
            "derived": True,
            "created_by": self.created_by,
        }

    def is_numerical(self) -> bool:
        return False

    def is_categorical(self) -> bool:
        return True

    def categories(self) -> list[str]:
        return list(self._enumerations)

    def summary(self) -> dict[str, Any]:
        return self.metadata()
