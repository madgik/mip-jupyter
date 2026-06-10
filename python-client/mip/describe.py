"""Descriptive statistics namespace."""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Mapping
from typing import Sequence

from .filters import FilterGroup
from .results import ResultTable
from . import _requests

_GLOBAL_DATASET_LABELS = {"all datasets", "all_datasets", "global"}


class DescribeNamespace:
    def __init__(self, analysis):
        self._analysis = analysis

    def numeric(
        self,
        *,
        variables: Sequence[str],
        group_by: str | None = None,
        levels: Sequence[str] | None = None,
        metrics: Sequence[str] | None = None,
        rename: Mapping[str, str] | None = None,
    ) -> ResultTable:
        metrics = list(metrics or ["num_dtps", "num_na", "num_total", "mean", "std", "q2"])
        rename = dict(rename or {})
        rows: List[dict] = []
        raw_payloads: List[Any] = []
        job_id = None

        cohort_levels = list(levels or [])
        if group_by and cohort_levels:
            for level in cohort_levels:
                result, current_job_id, _ = _requests.run_transient(
                    self._analysis._get_client(),
                    name=f"Numeric describe: {group_by}={level}",
                    algorithm_name="describe",
                    context=self._analysis.context,
                    y=list(variables),
                    filters=_requests.cohort_level_filter(group_by, level),
                    missing="drop",
                    missing_variables=list(variables) + [group_by],
                )
                raw_payloads.append(result)
                job_id = job_id or current_job_id
                rows.extend(
                    _numeric_rows_for_level(
                        result,
                        variables=variables,
                        cohort=level,
                        metrics=metrics,
                        rename=rename,
                    )
                )
        else:
            result, job_id, _ = _requests.run_transient(
                self._analysis._get_client(),
                name="Numeric describe",
                algorithm_name="describe",
                context=self._analysis.context,
                y=list(variables),
                missing="drop",
                missing_variables=list(variables),
            )
            raw_payloads.append(result)
            rows.extend(
                _numeric_rows_for_level(
                    result,
                    variables=variables,
                    cohort=None,
                    metrics=metrics,
                    rename=rename,
                )
            )

        return ResultTable.from_rows(rows, raw=raw_payloads, job_id=job_id, status="success")

    def categorical(
        self,
        *,
        variables: Sequence[str],
        group_by: str | None = None,
        levels: Sequence[str] | None = None,
        denominator: str = "non_null",
    ) -> ResultTable:
        rows: List[dict] = []
        raw_payloads: List[Any] = []
        job_id = None
        cohort_levels = list(levels or [])

        if group_by and cohort_levels:
            for level in cohort_levels:
                result, current_job_id, _ = _requests.run_transient(
                    self._analysis._get_client(),
                    name=f"Categorical describe: {group_by}={level}",
                    algorithm_name="describe",
                    context=self._analysis.context,
                    y=list(variables),
                    filters=_requests.cohort_level_filter(group_by, level),
                    missing="drop",
                    missing_variables=list(variables) + [group_by],
                )
                raw_payloads.append(result)
                job_id = job_id or current_job_id
                rows.extend(
                    _categorical_rows_for_level(
                        result,
                        variables=variables,
                        cohort=level,
                        denominator=denominator,
                    )
                )
        else:
            result, job_id, _ = _requests.run_transient(
                self._analysis._get_client(),
                name="Categorical describe",
                algorithm_name="describe",
                context=self._analysis.context,
                y=list(variables),
                missing="drop",
                missing_variables=list(variables),
            )
            raw_payloads.append(result)
            rows.extend(
                _categorical_rows_for_level(
                    result,
                    variables=variables,
                    cohort=None,
                    denominator=denominator,
                )
            )

        return ResultTable.from_rows(rows, raw=raw_payloads, job_id=job_id, status="success")


def _numeric_rows_for_level(
    result: Any,
    *,
    variables: Sequence[str],
    cohort: str | None,
    metrics: Sequence[str],
    rename: Mapping[str, str],
) -> List[dict]:
    rows: List[dict] = []
    records = _featurewise_records(result)
    for variable in variables:
        record = _pick_global_record(records, variable)
        data = (record or {}).get("data") or {}
        row: Dict[str, Any] = {"cohort": cohort, "variable": variable}
        for metric in metrics:
            column = rename.get(metric, metric)
            row[column] = data.get(metric)
        rows.append(row)
    return rows


def _categorical_rows_for_level(
    result: Any,
    *,
    variables: Sequence[str],
    cohort: str | None,
    denominator: str,
) -> List[dict]:
    rows: List[dict] = []
    records = _featurewise_records(result)
    for variable in variables:
        record = _pick_global_record(records, variable)
        data = (record or {}).get("data") or {}
        counts = data.get("counts") or {}
        denom_value = data.get("num_dtps") if denominator == "non_null" else data.get("num_total")
        denom_value = int(denom_value or 0)
        for level, count in counts.items():
            count_value = int(count)
            percent = (count_value / denom_value * 100.0) if denom_value else None
            rows.append(
                {
                    "cohort": cohort,
                    "variable": variable,
                    "level": level,
                    "count": count_value,
                    "denominator": denom_value,
                    "percent": percent,
                }
            )
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
        if dataset in _GLOBAL_DATASET_LABELS:
            return record
    for record in records:
        if record.get("variable") == variable:
            return record
    return None
