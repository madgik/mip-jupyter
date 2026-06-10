"""MIP Python client package for notebook-based analysis."""

from __future__ import annotations

from . import catalog
from .analysis import Analysis
from .client import configure
from ._metadata_tree import MetadataTree
from .context import Context
from .errors import MipAlgorithmNotAvailable
from .errors import MipBackendError
from .errors import MipConfigurationError
from .errors import MipError
from .errors import MipTransformationError
from .errors import MipValidationError
from .filters import MISSING
from .filters import Case
from .filters import FilterGroup
from .filters import Rule
from .filters import Validation
from .report import Report
from .report import ReportSection
from .results import ChiSquaredResult
from .results import ModelResult
from .results import ResultTable

__all__ = [
    "Analysis",
    "MetadataTree",
    "catalog",
    "Case",
    "ChiSquaredResult",
    "Context",
    "FilterGroup",
    "MISSING",
    "MipAlgorithmNotAvailable",
    "MipBackendError",
    "MipConfigurationError",
    "MipError",
    "MipTransformationError",
    "MipValidationError",
    "ModelResult",
    "Report",
    "ReportSection",
    "ResultTable",
    "Rule",
    "Validation",
    "configure",
]
