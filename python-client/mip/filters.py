"""Filter DSL that serializes to platform-backend / Exaflow-compatible JSON."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Iterable
from typing import Mapping
from typing import Sequence

AND = "AND"
OR = "OR"

_OPERATOR_MAP = {
    "==": "equal",
    "!=": "not_equal",
    "in": "in",
    "not_in": "not_in",
    ">": "greater",
    ">=": "greater_or_equal",
    "<": "less",
    "<=": "less_or_equal",
    "is_null": "is_null",
    "not_null": "is_not_null",
    "equal": "equal",
    "not_equal": "not_equal",
    "greater": "greater",
    "greater_or_equal": "greater_or_equal",
    "less": "less",
    "less_or_equal": "less_or_equal",
    "is_not_null": "is_not_null",
    "between": "between",
    "not_between": "not_between",
}

MISSING = object()


@dataclass(frozen=True)
class Rule:
    """A single filter rule on one field."""

    field: str
    operator: str
    value: Any = None

    def to_dict(self) -> dict:
        field = self.field.strip()
        operator = _normalize_operator(self.operator)
        return {
            "id": field,
            "field": field,
            "operator": operator,
            "value": self.value,
            "type": _infer_value_type(self.value),
        }


@dataclass(frozen=True)
class FilterGroup:
    """A group of rules combined with AND or OR."""

    condition: str
    rules: tuple[Any, ...]

    @classmethod
    def and_(cls, *rules: Any) -> FilterGroup:
        return cls(condition=AND, rules=tuple(rules))

    @classmethod
    def or_(cls, *rules: Any) -> FilterGroup:
        return cls(condition=OR, rules=tuple(rules))

    def to_dict(self) -> dict:
        condition = str(self.condition or "").strip().upper()
        if condition not in (AND, OR):
            raise ValueError("condition must be AND or OR.")
        serialized = [_serialize_rule(rule) for rule in self.rules]
        if not serialized:
            raise ValueError("rules must contain at least one rule.")
        return {"condition": condition, "rules": serialized}


@dataclass(frozen=True)
class Validation:
    """Validation options for categorical-from-filters transformations."""

    mutually_exclusive: bool = True
    allow_unmatched: bool = True

    def to_dict(self) -> dict:
        return {
            "mutually_exclusive": self.mutually_exclusive,
            "allow_unmatched": self.allow_unmatched,
        }


@dataclass(frozen=True)
class Case:
    """A labeled cohort case defined by a filter group."""

    label: str
    when: FilterGroup | Rule

    def to_dict(self) -> dict:
        when_dict = self.when.to_dict() if isinstance(self.when, FilterGroup) else self.when.to_dict()
        return {"label": self.label, "when": when_dict}


def merge_filter_groups(base: FilterGroup | None, extra: FilterGroup | Rule | None) -> FilterGroup | None:
    """Combine two filter groups with AND semantics."""
    if base is None and extra is None:
        return None
    if base is None:
        if isinstance(extra, Rule):
            return FilterGroup.and_(extra)
        return extra
    if extra is None:
        return base
    extra_rules: Sequence[Any]
    if isinstance(extra, Rule):
        extra_rules = (extra,)
    else:
        extra_rules = extra.rules
    return FilterGroup.and_(*base.rules, *extra_rules)


def _normalize_operator(operator: str) -> str:
    key = str(operator or "").strip()
    if key not in _OPERATOR_MAP:
        raise ValueError(f"Unsupported operator: {operator!r}")
    return _OPERATOR_MAP[key]


def _serialize_rule(rule: Any) -> dict:
    if isinstance(rule, Rule):
        return rule.to_dict()
    if isinstance(rule, FilterGroup):
        return rule.to_dict()
    if isinstance(rule, Mapping):
        rule_dict = dict(rule)
        if "condition" in rule_dict:
            return FilterGroup(
                condition=rule_dict["condition"],
                rules=tuple(rule_dict.get("rules") or []),
            ).to_dict()
        if "id" not in rule_dict and "field" in rule_dict:
            rule_dict["id"] = rule_dict["field"]
        if "field" not in rule_dict and "id" in rule_dict:
            rule_dict["field"] = rule_dict["id"]
        if "type" not in rule_dict:
            rule_dict["type"] = _infer_value_type(rule_dict.get("value"))
        if "operator" in rule_dict:
            rule_dict["operator"] = _normalize_operator(rule_dict["operator"])
        return rule_dict
    if isinstance(rule, tuple):
        if len(rule) == 3:
            field, operator, value = rule
            return Rule(field=field, operator=operator, value=value).to_dict()
        if len(rule) == 4:
            field, operator, value, value_type = rule
            payload = Rule(field=field, operator=operator, value=value).to_dict()
            payload["type"] = value_type
            return payload
    raise ValueError("Each rule must be a Rule, FilterGroup, dict, or tuple.")


def _infer_value_type(value: Any) -> str:
    if value is MISSING:
        return "string"
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
