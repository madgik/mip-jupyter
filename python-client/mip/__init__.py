"""MIP Python client package."""

from __future__ import annotations

from .algorithm import Algorithm
from .client import configure, get_client
from .data_model import DataModel
from .discovery import as_table, search_api, show_api
from .experiment import Experiment
from .mip_linear_regression import FederatedLinearRegression
from .mip_logistic_regression import FederatedLogisticRegression
from .mip_naive_bayes import FederatedNaiveBayes

from . import algorithms
from . import experiments
from . import filters
from . import metadata

__all__ = [
    "configure",
    "get_client",
    "Experiment",
    "Algorithm",
    "DataModel",
    "show_api",
    "search_api",
    "as_table",
    "metadata",
    "algorithms",
    "experiments",
    "filters",
    "FederatedLogisticRegression",
    "FederatedLinearRegression",
    "FederatedNaiveBayes",
]
