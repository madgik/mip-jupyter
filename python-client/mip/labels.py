"""Label-first helpers; internal codes are used only for backend payloads."""

from __future__ import annotations

import re
from typing import Any
from typing import Iterable
from typing import Mapping
from typing import Sequence


def normalize_label(text: Any) -> str:
    return str(text or "").strip().casefold()


def slug_from_label(label: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", str(label).strip().lower()).strip("_")
    return text or "derived"


def internal_code(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "_code"):
        code = getattr(value, "_code")
        if code is not None:
            return str(code)
    if hasattr(value, "_name"):
        name = getattr(value, "_name")
        if name is not None:
            return str(name)
    if hasattr(value, "code"):
        code = getattr(value, "code")
        if code is not None:
            return str(code)
    return str(value)


def public_label(value: Any) -> str:
    if value is None:
        return ""
    label = getattr(value, "label", None)
    if label is not None and str(label).strip():
        return str(label)
    return str(value)


def enumeration_labels(raw_enums: Any) -> list[str]:
    if isinstance(raw_enums, Mapping):
        labels: list[str] = []
        for key, value in raw_enums.items():
            text = str(value).strip() if value is not None else ""
            labels.append(text or str(key))
        return labels
    if isinstance(raw_enums, (list, tuple)):
        return [str(item) for item in raw_enums]
    return []


def enumeration_code_for_label(raw_enums: Any, label: Any) -> str | None:
    needle = normalize_label(label)
    if isinstance(raw_enums, Mapping):
        for key, value in raw_enums.items():
            if normalize_label(key) == needle:
                return str(key)
            if normalize_label(value) == needle:
                return str(key)
        return None
    if isinstance(raw_enums, (list, tuple)):
        for item in raw_enums:
            if normalize_label(item) == needle:
                return str(item)
    return None


def lookup_by_label(items: Sequence[Any], label: str, *, kind: str = "item") -> Any:
    needle = normalize_label(label)
    matches = [item for item in items if normalize_label(public_label(item)) == needle]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        available = ", ".join(sorted({public_label(item) for item in matches}))
        raise LookupError(f"Ambiguous {kind} label {label!r}. Matches: {available}")
    available = ", ".join(sorted({public_label(item) for item in items}))
    raise KeyError(f"Unknown {kind} label: {label!r}. Available: {available}")


def build_code_to_label_lookup(*collections: Iterable[Any]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for collection in collections:
        for item in collection:
            code = internal_code(item)
            if code:
                lookup[code] = public_label(item)
    return lookup


def sanitize_mapping_keys(mapping: Mapping[Any, Any] | None, lookup: Mapping[str, str]) -> dict[str, Any]:
    if not mapping:
        return {}
    sanitized: dict[str, Any] = {}
    for key, value in mapping.items():
        code = internal_code(key)
        sanitized[lookup.get(code, public_label(key))] = value
    return sanitized


def sanitize_filter_payload(payload: Any, lookup: Mapping[str, str]) -> Any:
    if not isinstance(payload, dict):
        return payload
    if "condition" in payload:
        return {
            "condition": payload.get("condition"),
            "rules": [sanitize_filter_payload(rule, lookup) for rule in payload.get("rules") or []],
        }
    copied = dict(payload)
    field = str(copied.get("field") or copied.get("id") or "")
    if field in lookup:
        copied["field"] = lookup[field]
        copied["id"] = lookup[field]
    value = copied.get("value")
    if isinstance(value, list):
        copied["value"] = [_sanitize_filter_value(item, lookup) for item in value]
    elif value is not None:
        copied["value"] = _sanitize_filter_value(value, lookup)
    return copied


def _sanitize_filter_value(value: Any, lookup: Mapping[str, str]) -> Any:
    text = str(value)
    return lookup.get(text, value)


def sanitize_preprocessing_steps(steps: Sequence[Any] | None, lookup: Mapping[str, str]) -> list[dict[str, Any]] | None:
    if not steps:
        return None
    sanitized: list[dict[str, Any]] = []
    for step in steps:
        if hasattr(step, "user_summary"):
            sanitized.append(step.user_summary())
            continue
        if isinstance(step, dict):
            sanitized.append(_sanitize_preprocessing_dict(step, lookup))
    return sanitized or None


def _sanitize_preprocessing_dict(step: dict[str, Any], lookup: Mapping[str, str]) -> dict[str, Any]:
    copied = {"name": step.get("name")}
    parameters = dict(step.get("parameters") or {})
    sanitized_parameters: dict[str, Any] = {}
    for key, value in parameters.items():
        if key in {"strategies", "tails", "folds", "fill_values"} and isinstance(value, Mapping):
            sanitized_parameters[key] = sanitize_mapping_keys(value, lookup)
        elif key == "rules" and isinstance(value, Mapping):
            sanitized_parameters[key] = {str(rule_label): rule for rule_label, rule in value.items()}
        elif key == "code":
            continue
        else:
            sanitized_parameters[key] = value
    if sanitized_parameters:
        copied["parameters"] = sanitized_parameters
    return copied


def sanitize_explain_dict(payload: dict[str, Any], *, lookup: Mapping[str, str]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in payload.items():
        if key == "analysis_set" and isinstance(value, dict):
            sanitized[key] = {
                "data_model": value.get("data_model"),
                "datasets": list(value.get("datasets") or []),
                "variables": list(value.get("variables") or []),
            }
        elif key == "filters":
            sanitized[key] = sanitize_filter_payload(value, lookup)
        elif key == "preprocessing":
            if isinstance(value, list):
                sanitized[key] = [_sanitize_preprocessing_dict(item, lookup) for item in value]
            else:
                sanitized[key] = value
        elif key == "new_columns" and isinstance(value, list):
            sanitized[key] = value
        else:
            sanitized[key] = value
    return sanitized


def sanitize_inputdata(payload: dict[str, Any], *, lookup: Mapping[str, str]) -> dict[str, Any]:
    datasets = payload.get("datasets") or []
    variables = payload.get("variables") or []
    return {
        "data_model": payload.get("data_model"),
        "datasets": [lookup.get(str(item), str(item)) for item in datasets],
        "validation_datasets": payload.get("validation_datasets"),
        "filters": sanitize_filter_payload(payload.get("filters"), lookup),
        "variables": [lookup.get(str(item), str(item)) for item in variables],
    }


def list_group_summaries(groups: Iterable[Any]) -> list[dict[str, Any]]:
    from .metadata_tree import list_groups

    return [
        {"label": item.get("label") or item.get("path", [""])[-1], "path": item.get("path") or []}
        for item in list_groups(groups)
        if item.get("label") or item.get("path")
    ]
