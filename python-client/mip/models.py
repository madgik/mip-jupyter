"""Model fitting namespace."""

from __future__ import annotations

import math
from typing import Any
from typing import Dict
from typing import List
from typing import Mapping
from typing import Sequence

from .results import ModelResult
from . import _requests


class ModelsNamespace:
    def __init__(self, analysis):
        self._analysis = analysis

    def logistic_regression(
        self,
        *,
        outcome: str,
        positive_class: str,
        predictors: Sequence[str],
        reference_levels: Mapping[str, str] | None = None,
        missing: str = "drop",
    ) -> ModelResult:
        result, job_id, status = _requests.run_transient(
            self._analysis._get_client(),
            name=f"Logistic regression: {outcome}",
            algorithm_name="logistic_regression",
            context=self._analysis.context,
            x=list(predictors),
            y=[outcome],
            parameters={"positive_class": positive_class},
            missing=missing,
            missing_variables=[outcome, *predictors],
        )
        summary_rows, metrics_rows = _parse_logistic_regression(
            result,
            reference_levels=reference_levels or {},
        )
        return ModelResult(
            rows=summary_rows,
            summary_rows=summary_rows,
            metrics_rows=metrics_rows,
            raw=result,
            job_id=job_id,
            status=status,
        )


def _parse_logistic_regression(
    result: Any,
    *,
    reference_levels: Mapping[str, str],
) -> tuple[List[dict], List[dict]]:
    payload = result if isinstance(result, dict) else {}
    summary = payload.get("summary") or {}
    indep_vars = payload.get("indep_vars") or []
    summary_feature_names = summary.get("feature_names")
    if isinstance(summary_feature_names, list) and summary_feature_names:
        feature_names = list(summary_feature_names)
    elif indep_vars and indep_vars[0] == "Intercept":
        feature_names = list(indep_vars)
    else:
        feature_names = ["Intercept"] + list(indep_vars)

    coefficients = summary.get("coefficients") or []
    stderr = summary.get("stderr") or []
    z_scores = summary.get("z_scores") or []
    pvalues = summary.get("pvalues") or []
    lower_ci = summary.get("lower_ci") or []
    upper_ci = summary.get("upper_ci") or []

    summary_rows: List[dict] = []
    for index, term in enumerate(feature_names):
        coef = _safe_index(coefficients, index)
        summary_rows.append(
            {
                "term": term,
                "coefficient": coef,
                "odds_ratio": math.exp(coef) if coef is not None else None,
                "std_error": _safe_index(stderr, index),
                "z_score": _safe_index(z_scores, index),
                "p_value": _safe_index(pvalues, index),
                "ci_low": _safe_index(lower_ci, index),
                "ci_high": _safe_index(upper_ci, index),
                "reference_level": reference_levels.get(term),
            }
        )

    metrics_rows = [
        {
            "n_obs": summary.get("n_obs"),
            "df_model": summary.get("df_model"),
            "df_resid": summary.get("df_resid"),
            "r_squared_cs": summary.get("r_squared_cs"),
            "r_squared_mcf": summary.get("r_squared_mcf"),
            "ll0": summary.get("ll0"),
            "ll": summary.get("ll"),
            "aic": summary.get("aic"),
            "bic": summary.get("bic"),
        }
    ]
    return summary_rows, metrics_rows


def _safe_index(values: Sequence[Any], index: int):
    if index < len(values):
        return values[index]
    return None
