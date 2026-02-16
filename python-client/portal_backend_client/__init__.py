"""Portal Backend Python client.

Public API:
- configure(...)
- get_client()
- Experiment
- DataModel
- show_api(...)
- search_api(...)
- as_table(...)
"""

from .client import configure, get_client
from .experiment import Experiment
from .data_model import DataModel
from .discovery import show_api, search_api, as_table

__all__ = [
    "configure",
    "get_client",
    "Experiment",
    "DataModel",
    "show_api",
    "search_api",
    "as_table",
]
