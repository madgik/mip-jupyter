"""Statistical tests namespace."""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Sequence

from .results import ChiSquaredResult
from .results import ResultTable
from . import _requests


class TestsNamespace:
    def __init__(self, analysis):
        self._analysis = analysis

    def ttest_independent(
        self,
        *,
        variables: Sequence[str],
        group_by: str,
        group_a: str,
        group_b: str,
        alpha: float = 0.05,
        alternative: str = "two-sided",
        missing: str = "drop",
    ) -> ResultTable:
        rows: List[dict] = []
        raw_payloads: List[Any] = []
        job_id = None
        parameters = {
            "groupA": group_a,
            "groupB": group_b,
            "alpha": alpha,
            "alt_hypothesis": _requests.alternative_to_alt_hypothesis(alternative),
        }

        for variable in variables:
            result, current_job_id, _ = _requests.run_transient(
                self._analysis._get_client(),
                name=f"T-test: {variable}",
                algorithm_name="ttest_independent",
                context=self._analysis.context,
                x=[group_by],
                y=[variable],
                parameters=parameters,
                missing=missing,
                missing_variables=[group_by, variable],
            )
            raw_payloads.append(result)
            job_id = job_id or current_job_id
            rows.append(_ttest_row(variable, group_a, group_b, result))

        return ResultTable.from_rows(rows, raw=raw_payloads, job_id=job_id, status="success")

    def mann_whitney_u(
        self,
        *,
        variables: Sequence[str],
        group_by: str,
        group_a: str,
        group_b: str,
        alternative: str = "two-sided",
        missing: str = "drop",
    ) -> ResultTable:
        raise NotImplementedError("Mann-Whitney U is not available yet in the backend.")

    def chi_squared(
        self,
        *,
        factor: str,
        outcomes: Sequence[str],
        missing: str = "drop",
    ) -> ChiSquaredResult:
        rows: List[dict] = []
        raw_payloads: List[Any] = []
        contingency_tables: Dict[str, Any] = {}
        job_id = None

        for outcome in outcomes:
            result, current_job_id, _ = _requests.run_transient(
                self._analysis._get_client(),
                name=f"Chi-squared: {factor} vs {outcome}",
                algorithm_name="chi_squared",
                context=self._analysis.context,
                x=[factor],
                y=[outcome],
                missing=missing,
                missing_variables=[factor, outcome],
            )
            raw_payloads.append(result)
            job_id = job_id or current_job_id
            rows.append(_chi_squared_row(factor, outcome, result))
            table = _contingency_table(result)
            if table is not None:
                contingency_tables[outcome] = table

        return ChiSquaredResult(
            rows=rows,
            raw=raw_payloads,
            job_id=job_id,
            status="success",
            contingency_tables=contingency_tables,
        )


def _ttest_row(variable: str, group_a: str, group_b: str, result: Any) -> dict:
    payload = result if isinstance(result, dict) else {}
    return {
        "variable": variable,
        "group_a": group_a,
        "group_b": group_b,
        "t_stat": payload.get("t_stat"),
        "df": payload.get("df"),
        "p_value": payload.get("p"),
        "mean_diff": payload.get("mean_diff"),
        "se_diff": payload.get("se_diff"),
        "ci_low": payload.get("ci_lower"),
        "ci_high": payload.get("ci_upper"),
        "cohens_d": payload.get("cohens_d"),
    }


def _chi_squared_row(factor: str, outcome: str, result: Any) -> dict:
    payload = result if isinstance(result, dict) else {}
    return {
        "factor": factor,
        "outcome": outcome,
        "chi2": payload.get("chi2"),
        "p_value": payload.get("p_value"),
        "dof": payload.get("dof"),
    }


def _contingency_table(result: Any):
    import pandas as pd

    if not isinstance(result, dict):
        return None
    expected = result.get("expected")
    x_labels = result.get("x_labels") or []
    y_labels = result.get("y_labels") or []
    if not expected or not x_labels or not y_labels:
        return None
    return pd.DataFrame(expected, index=x_labels, columns=y_labels)
