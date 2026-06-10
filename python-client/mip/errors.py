"""Notebook-friendly exception types for the MIP library."""


class MipError(Exception):
    """Base class for MIP library errors."""


class MipConfigurationError(MipError):
    """Raised when no platform-backend client is configured."""


class MipBackendError(MipError):
    """Raised when a platform-backend request or experiment fails."""


class MipAlgorithmNotAvailable(MipError):
    """Raised when a requested algorithm is not available on the backend."""


class MipValidationError(MipError):
    """Raised when user input fails validation."""


class MipTransformationError(MipError):
    """Raised when a transformation cannot be applied or serialized."""
