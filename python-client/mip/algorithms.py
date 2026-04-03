"""Algorithm catalog helpers for notebook users."""

from __future__ import annotations

from typing import List

from .algorithm import Algorithm


def list() -> List[Algorithm]:  # noqa: A001 - public API follows notebook convention
    """List algorithms available to the current user."""
    return Algorithm.list()
