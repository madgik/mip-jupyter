"""Filter DSL helpers that serialize to Platform Backend/Exaflow format."""

from __future__ import annotations

from typing import Any
from typing import Iterable
from typing import Mapping

# Group conditions
AND = "AND"
OR = "OR"

# Operators (backend/exaflow expects these lower-case values)
EQUAL = "equal"
NOT_EQUAL = "not_equal"
LESS = "less"
GREATER = "greater"
LESS_OR_EQUAL = "less_or_equal"
GREATER_OR_EQUAL = "greater_or_equal"
BETWEEN = "between"
NOT_BETWEEN = "not_between"
IS_NULL = "is_null"
IS_NOT_NULL = "is_not_null"
IN = "in"
NOT_IN = "not_in"


def RULE(field: str, operator: str, value: Any, value_type: str | None = None) -> dict:
    """Build a single backend-compatible filter rule."""
    if not isinstance(field, str) or not field.strip():
        raise ValueError("field must be a non-empty string.")
    if not isinstance(operator, str) or not operator.strip():
        raise ValueError("operator must be a non-empty string.")

    return {
        "id": field.strip(),
        "field": field.strip(),
        "operator": operator.strip(),
        "value": value,
        "type": value_type or _infer_value_type(value),
    }


def RULESET(rules: Iterable[Any], condition: str = AND) -> dict:
    """Build a backend-compatible ruleset payload.

    Rules may be provided as:
    - rule dicts (already serialized)
    - tuples: (field, operator, value)
    - tuples: (field, operator, value, value_type)
    """
    condition_value = str(condition or "").strip().upper()
    if condition_value not in (AND, OR):
        raise ValueError("condition must be AND or OR.")

    serialized_rules = [_normalize_rule(rule) for rule in (rules or [])]
    if not serialized_rules:
        raise ValueError("rules must contain at least one rule.")

    return {
        "condition": condition_value,
        "rules": serialized_rules,
    }


def _normalize_rule(rule: Any) -> dict:
    if isinstance(rule, Mapping):
        rule_dict = dict(rule)
        is_leaf_rule = "id" in rule_dict or "field" in rule_dict
        if "id" not in rule_dict and "field" in rule_dict:
            rule_dict["id"] = rule_dict["field"]
        if "field" not in rule_dict and "id" in rule_dict:
            rule_dict["field"] = rule_dict["id"]
        if is_leaf_rule and "type" not in rule_dict:
            rule_dict["type"] = _infer_value_type(rule_dict.get("value"))
        return rule_dict

    if isinstance(rule, tuple):
        if len(rule) == 3:
            field, operator, value = rule
            return RULE(field=field, operator=operator, value=value)
        if len(rule) == 4:
            field, operator, value, value_type = rule
            return RULE(field=field, operator=operator, value=value, value_type=value_type)

    raise ValueError(
        "Each rule must be a dict, (field, operator, value), or "
        "(field, operator, value, value_type)."
    )


def _infer_value_type(value: Any) -> str:
    if isinstance(value, list):
        for item in value:
            if item is not None:
                return _infer_value_type(item)
        return "string"

    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "double"
    return "string"
