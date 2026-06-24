"""Catalog access for backend data models, variables, and datasets."""

from __future__ import annotations

from .datamodel import DataModel
from .display import HelpText
from .labels import normalize_label
from .labels import public_label
from .metadata_tree import MetadataTree
from .metadata_tree import render_catalog_tree


class Catalog:
    """Data-model discovery facade."""

    def __init__(self, transport):
        self._transport = transport

    def data_models(self) -> list[DataModel]:
        payload = self._transport.get("/data-models")
        if not isinstance(payload, list):
            return []
        return [DataModel(item, transport=self._transport) for item in payload if isinstance(item, dict)]

    def list(self) -> list[DataModel]:
        """Return all authorized data models."""
        return self.data_models()

    def summaries(self) -> list[dict]:
        """Return compact summaries for choosing a data model in notebooks."""
        return [model.summary() for model in self.data_models()]

    def tree(self, *, max_lines: int = 250) -> MetadataTree:
        """Render an ASCII tree of all authorized data models."""
        return MetadataTree(render_catalog_tree(self.data_models(), max_lines=max_lines))

    def data_model(self, label: str, version: str | None = None) -> DataModel:
        needle = normalize_label(label)
        matches = [model for model in self.data_models() if normalize_label(model.label) == needle]
        if version is not None:
            for model in matches:
                if str(model.version) == str(version):
                    return model
            raise LookupError(f"No data model found for {label!r} version {version!r}.")
        if not matches:
            available = ", ".join(sorted({public_label(model) for model in self.data_models()}))
            raise LookupError(f"No data model found for {label!r}. Available: {available}")
        if len(matches) > 1:
            available = ", ".join(sorted({model.name for model in matches}))
            raise LookupError(
                "Multiple data model versions found. Pass version explicitly. "
                f"Available for {label!r}: {available}"
            )
        return matches[0]

    def search_variables(self, text: str = "") -> list:
        results = []
        for model in self.data_models():
            results.extend(model.variables.search(text))
        return results

    def search_datasets(self, text: str = "") -> list:
        results = []
        for model in self.data_models():
            results.extend(model.datasets.search(text))
        return results

    def help(self) -> HelpText:
        from .display import show_help

        return show_help("Catalog")
