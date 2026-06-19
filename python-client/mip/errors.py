"""Backward-compatible aliases for public exception types."""

from __future__ import annotations

from .exceptions import MipAlgorithmNotAvailable
from .exceptions import MipBackendError
from .exceptions import MipConfigurationError
from .exceptions import MipError
from .exceptions import UnsupportedOperationError

__all__ = [
    "MipAlgorithmNotAvailable",
    "MipBackendError",
    "MipConfigurationError",
    "MipError",
    "UnsupportedOperationError",
]
