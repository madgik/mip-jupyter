"""Data model metadata from platform-backend."""

from __future__ import annotations

from typing import Any
from typing import List
from typing import Mapping
from typing import Optional

from .client import get_client


class DataModel:
    """Data model metadata and datasets available for analysis."""

    def __init__(self, data: Mapping[str, Any]):
        self.code = data.get("code")
        self.version = data.get("version")
        self.label = data.get("label")
        self.longitudinal = data.get("longitudinal")
        self.variables = data.get("variables", [])
        self.groups = data.get("groups", [])
        self.datasets = data.get("datasets", [])
        self.datasets_variables = data.get("datasetsVariables", data.get("datasets_variables", {}))

    def __repr__(self) -> str:
        return f"<DataModel(code='{self.code}', version='{self.version}')>"

    @property
    def name(self) -> str:
        code = self.code or ""
        version = self.version or ""
        if code and version:
            return f"{code}:{version}"
        return code or str(version or "")

    @classmethod
    def list(cls, client=None) -> List[DataModel]:
        """List all data models visible to the current user."""
        backend_client = client or get_client()
        data = backend_client.get("/data-models")
        if not isinstance(data, list):
            return []
        return [cls(item) for item in data if isinstance(item, Mapping)]


def resolve_data_model(selector: str, models: List[DataModel]) -> DataModel:
    """Resolve a data model by `code:version` or unambiguous `code`."""
    if not isinstance(selector, str) or not selector.strip():
        raise ValueError("data_model must be a non-empty string.")

    key = selector.strip()
    if ":" in key:
        code, version = key.split(":", 1)
        for model in models:
            if model.code == code and str(model.version) == version:
                return model
        raise LookupError(f"No data model found for '{key}'.")

    matched = [model for model in models if model.code == key]
    if not matched:
        raise LookupError(f"No data model found for '{key}'.")
    if len(matched) > 1:
        available = ", ".join(sorted(model.name for model in matched))
        raise LookupError(
            "Multiple data model versions found. Use '<code>:<version>'. "
            f"Available for '{key}': {available}"
        )
    return matched[0]
