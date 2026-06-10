"""Result wrappers for notebook-friendly analysis output."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import pandas as pd


@dataclass
class ResultTable:
    """Tabular analysis result with optional raw backend payload."""

    rows: List[Dict[str, Any]] = field(default_factory=list)
    raw: Any = None
    job_id: Optional[str] = None
    status: Optional[str] = None

    def to_dataframe(self) -> pd.DataFrame:
        if not self.rows:
            return pd.DataFrame()
        return pd.DataFrame(self.rows)

    @classmethod
    def from_rows(
        cls,
        rows: List[Dict[str, Any]],
        *,
        raw: Any = None,
        job_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> ResultTable:
        return cls(rows=list(rows or []), raw=raw, job_id=job_id, status=status)


@dataclass
class ModelResult(ResultTable):
    """Model output with separate summary and metrics tables."""

    summary_rows: List[Dict[str, Any]] = field(default_factory=list)
    metrics_rows: List[Dict[str, Any]] = field(default_factory=list)

    def summary(self) -> ResultTable:
        return ResultTable.from_rows(
            self.summary_rows,
            raw=self.raw,
            job_id=self.job_id,
            status=self.status,
        )

    def metrics(self) -> ResultTable:
        return ResultTable.from_rows(
            self.metrics_rows,
            raw=self.raw,
            job_id=self.job_id,
            status=self.status,
        )


@dataclass
class ChiSquaredResult(ResultTable):
    """Chi-squared result with optional contingency tables per outcome."""

    contingency_tables: Dict[str, pd.DataFrame] = field(default_factory=dict)
