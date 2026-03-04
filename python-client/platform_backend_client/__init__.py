"""Platform Backend Python client.

Public API:
- configure(...)
- get_client()
- Experiment
- Algorithm
- DataModel
- FederatedLogisticRegression
- FederatedLinearRegression
- FederatedNaiveBayes
- show_api(...)
- search_api(...)
- as_table(...)
"""

from .client import configure, get_client
from .experiment import Experiment
from .algorithm import Algorithm
from .data_model import DataModel
from .discovery import show_api, search_api, as_table
from .mip_logistic_regression import FederatedLogisticRegression
from .mip_linear_regression import FederatedLinearRegression
from .mip_naive_bayes import FederatedNaiveBayes

__all__ = [
    "configure",
    "get_client",
    "Experiment",
    "Algorithm",
    "DataModel",
    "FederatedLogisticRegression",
    "FederatedLinearRegression",
    "FederatedNaiveBayes",
    "show_api",
    "search_api",
    "as_table",
]
