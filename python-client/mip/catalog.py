"""Pre-Context catalog for data models, datasets, and metadata visualization."""

from __future__ import annotations

from typing import Any
from typing import List
from typing import Mapping
from typing import Optional

from . import _metadata_tree
from ._metadata_tree import MetadataTree
from .data_model import DataModel
from .data_model import resolve_data_model
from .results import ResultTable


def _load_models(client=None) -> List[DataModel]:
    return DataModel.list(client=client)


def _dataset_code(dataset: Any) -> str:
    if isinstance(dataset, str):
        return dataset
    if isinstance(dataset, Mapping):
        return str(dataset.get("code") or dataset.get("label") or "").strip()
    return str(getattr(dataset, "code", "") or getattr(dataset, "label", "") or "").strip()


def _dataset_label(dataset: Any) -> str:
    if isinstance(dataset, str):
        return dataset
    if isinstance(dataset, Mapping):
        return str(dataset.get("label") or dataset.get("code") or "").strip()
    return str(getattr(dataset, "label", "") or getattr(dataset, "code", "") or "").strip()


def models(*, client=None) -> ResultTable:
    """List all authorized data models as a browseable table."""
    items = _load_models(client=client)
    rows = []
    for model in items:
        rows.append(
            {
                "name": model.name,
                "code": model.code,
                "version": model.version,
                "label": model.label,
                "longitudinal": model.longitudinal,
                "n_datasets": len(model.datasets or []),
                "n_groups": _metadata_tree._count_group_nodes(model.groups or []),
            }
        )
    return ResultTable.from_rows(rows, raw=items, status="success")


def datasets(data_model: str, *, client=None) -> ResultTable:
    """List datasets available for a data model."""
    items = _load_models(client=client)
    model = resolve_data_model(data_model, items)
    rows = []
    for dataset in model.datasets or []:
        rows.append(
            {
                "data_model": model.name,
                "code": _dataset_code(dataset),
                "label": _dataset_label(dataset),
            }
        )
    return ResultTable.from_rows(rows, raw=model.datasets, status="success")


def get(data_model: str, *, client=None) -> DataModel:
    """Return full metadata for one data model."""
    items = _load_models(client=client)
    return resolve_data_model(data_model, items)


def visualize(
    data_model: str,
    *,
    include_variables: bool = False,
    max_lines: int = 250,
    client=None,
) -> MetadataTree:
    """Render an ASCII metadata tree for one data model."""
    model = get(data_model, client=client)
    pathology = _metadata_tree.pathology_from_model(model)
    text = _metadata_tree.render_pathology_tree(
        pathology,
        include_variables=include_variables,
        max_lines=max_lines,
    )
    return MetadataTree(text)


def visualize_all(*, max_lines: int = 250, client=None) -> MetadataTree:
    """Render a compact catalog tree of all data models."""
    items = _load_models(client=client)
    text = _metadata_tree.render_catalog_tree(items, max_lines=max_lines)
    return MetadataTree(text)
