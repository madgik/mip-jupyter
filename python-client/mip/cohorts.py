"""Cohort validation namespace."""

from __future__ import annotations

from typing import Any
from typing import List
from typing import Sequence

from .errors import MipValidationError
from .filters import FilterGroup
from .filters import Rule
from .results import ResultTable
from .transformations import CategoricalFromFilters
from . import _requests


class CohortsNamespace:
    def __init__(self, analysis):
        self._analysis = analysis

    def validate(
        self,
        *,
        group_by: str,
        expected_levels: Sequence[str],
        checks: Sequence[str] | None = None,
    ) -> ResultTable:
        checks = list(checks or ["mutual_exclusivity", "counts", "missing"])
        context = self._analysis.context
        transformation = _find_transformation(context.transformations, group_by)

        rows: List[dict] = []
        raw_payloads: List[Any] = []
        job_ids: List[str] = []

        if "mutual_exclusivity" in checks and transformation is not None:
            rows.extend(_structural_mutual_exclusivity_rows(transformation))

        if any(check in checks for check in ("counts", "missing")):
            result, job_id, status = _requests.run_transient(
                self._analysis._get_client(),
                name=f"Cohort validation: {group_by}",
                algorithm_name="describe",
                context=context,
                y=[group_by],
                missing="drop",
                missing_variables=[group_by],
            )
            raw_payloads.append(result)
            if job_id:
                job_ids.append(job_id)
            rows.extend(_describe_validation_rows(result, group_by, expected_levels, checks))

        if not rows:
            for level in expected_levels:
                rows.append({"level": level, "count": None, "missing": None, "overlap_flag": None})

        return ResultTable.from_rows(
            rows,
            raw=raw_payloads,
            job_id=job_ids[0] if job_ids else None,
            status="success",
        )


def _find_transformation(transformations, name: str) -> CategoricalFromFilters | None:
    for item in transformations or ():
        if isinstance(item, CategoricalFromFilters) and item.name == name:
            return item
    return None


def _structural_mutual_exclusivity_rows(transformation: CategoricalFromFilters) -> List[dict]:
    rows: List[dict] = []
    if transformation.validation and not transformation.validation.mutually_exclusive:
        return rows
    labels = [case.label for case in transformation.cases]
    if len(labels) != len(set(labels)):
        raise MipValidationError("Transformation cases must have unique labels.")
    for label in labels:
        rows.append(
            {
                "level": label,
                "count": None,
                "missing": None,
                "overlap_flag": False,
                "check": "mutual_exclusivity",
            }
        )
    return rows


def _describe_validation_rows(
    result: Any,
    group_by: str,
    expected_levels: Sequence[str],
    checks: Sequence[str],
) -> List[dict]:
    rows: List[dict] = []
    records = _featurewise_records(result)
    global_record = _pick_global_record(records, group_by)
    data = (global_record or {}).get("data") or {}
    counts = data.get("counts") or {}
    num_na = data.get("num_na")
    total_count = sum(int(value) for value in counts.values()) if counts else 0
    overlap_flag = total_count > 0 and len(counts) > len(expected_levels)

    for level in expected_levels:
        row = {
            "level": level,
            "count": int(counts.get(level, 0)) if "counts" in checks else None,
            "missing": int(num_na) if "missing" in checks and num_na is not None else None,
            "overlap_flag": overlap_flag if "mutual_exclusivity" in checks else None,
        }
        rows.append(row)
    return rows


def _featurewise_records(result: Any) -> List[dict]:
    if isinstance(result, dict):
        featurewise = result.get("featurewise") or []
        return [item for item in featurewise if isinstance(item, dict)]
    return []


def _pick_global_record(records: List[dict], variable: str) -> dict | None:
    for record in records:
        if record.get("variable") != variable:
            continue
        dataset = str(record.get("dataset") or "").lower()
        if dataset in {"all datasets", "all_datasets", "global"}:
            return record
    for record in records:
        if record.get("variable") == variable:
            return record
    return None
