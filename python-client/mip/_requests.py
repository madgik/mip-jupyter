"""Shared platform-backend transient experiment request helpers."""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Sequence

from .context import Context
from .errors import MipBackendError
from .filters import FilterGroup
from .filters import Rule
from .filters import merge_filter_groups
from .transformations import serialize_transformations


def build_preprocessing(
    context: Context,
    *,
    missing: str | None = None,
    variables: Sequence[str] | None = None,
    extra_preprocessing: Dict[str, Any] | None = None,
) -> dict:
    """Assemble preprocessing dict from context transformations and missing policy."""
    preprocessing: Dict[str, Any] = {}
    transformation_block = serialize_transformations(context.transformations)
    preprocessing.update(transformation_block)

    if missing == "drop" and variables:
        strategies = {var: "drop" for var in variables}
        preprocessing["missing_values_handler"] = {"strategies": strategies}

    if extra_preprocessing:
        preprocessing.update(extra_preprocessing)
    return preprocessing


def build_filters(
    context: Context,
    extra_filters: FilterGroup | Rule | None = None,
) -> dict | None:
    """Merge context filters with optional per-call filters."""
    merged = merge_filter_groups(context.filters, extra_filters)
    if merged is None:
        return None
    return merged.to_dict()


def build_transient_payload(
    *,
    name: str,
    algorithm_name: str,
    context: Context,
    x: Sequence[str] | None = None,
    y: Sequence[str] | None = None,
    parameters: Dict[str, Any] | None = None,
    preprocessing: Dict[str, Any] | None = None,
    filters: FilterGroup | Rule | None = None,
    missing: str | None = None,
    missing_variables: Sequence[str] | None = None,
) -> dict:
    """Build POST /experiments/transient JSON body."""
    x_vars = list(x or [])
    y_vars = list(y or [])
    all_vars = list(dict.fromkeys([*x_vars, *y_vars]))
    preprocessing_payload = build_preprocessing(
        context,
        missing=missing,
        variables=missing_variables or all_vars,
        extra_preprocessing=preprocessing,
    )
    return {
        "name": name,
        "mipVersion": context.mip_version,
        "algorithm": {
            "name": algorithm_name,
            "parameters": parameters or {},
            "preprocessing": preprocessing_payload,
            "inputdata": {
                "data_model": context.data_model,
                "datasets": list(context.datasets),
                "x": x_vars,
                "y": y_vars,
                "filters": build_filters(context, filters),
            },
        },
    }


def _extract_experiment_fields(data: dict) -> tuple[Any, Optional[str], Optional[str], Optional[str]]:
    status = data.get("status")
    uuid = data.get("uuid")
    results = data.get("result", data.get("results"))
    error_message = data.get("errorMessage") or data.get("error")
    if not error_message and isinstance(results, dict):
        error_message = (
            results.get("errorMessage")
            or results.get("error")
            or results.get("message")
        )
    return results, uuid, status, error_message


def run_transient(
    client,
    *,
    name: str,
    algorithm_name: str,
    context: Context,
    x: Sequence[str] | None = None,
    y: Sequence[str] | None = None,
    parameters: Dict[str, Any] | None = None,
    preprocessing: Dict[str, Any] | None = None,
    filters: FilterGroup | Rule | None = None,
    missing: str | None = None,
    missing_variables: Sequence[str] | None = None,
) -> tuple[Any, Optional[str], Optional[str]]:
    """Execute a transient experiment and return (result, job_id, status)."""
    payload = build_transient_payload(
        name=name,
        algorithm_name=algorithm_name,
        context=context,
        x=x,
        y=y,
        parameters=parameters,
        preprocessing=preprocessing,
        filters=filters,
        missing=missing,
        missing_variables=missing_variables,
    )
    try:
        data = client.post("/experiments/transient", data=payload)
    except Exception as exc:
        raise MipBackendError(f"Transient experiment request failed: {exc}") from exc

    results, uuid, status, error_message = _extract_experiment_fields(data or {})
    status_norm = (status or "").strip().lower()
    if status_norm in {"error", "failed", "failure"} or error_message:
        raise MipBackendError(
            "Transient experiment failed.\n"
            f"- uuid: {uuid}\n"
            f"- status: {status}\n"
            f"- details: {error_message or results}\n"
        )
    return results, uuid, status


def cohort_level_filter(group_by: str, level: str) -> Rule:
    """Build a filter rule for one cohort level."""
    return Rule(group_by, "==", level)


def alternative_to_alt_hypothesis(alternative: str) -> str:
    mapping = {
        "two-sided": "two-sided",
        "two_sided": "two-sided",
        "less": "less",
        "greater": "greater",
    }
    key = str(alternative or "two-sided").strip().lower()
    if key not in mapping:
        raise ValueError(f"Unsupported alternative: {alternative!r}")
    return mapping[key]
