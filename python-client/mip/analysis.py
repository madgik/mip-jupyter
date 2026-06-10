"""User-facing analysis object bound to a Context."""

from __future__ import annotations

from typing import Sequence

from .client import get_client
from .context import Context
from .errors import MipConfigurationError
from .transformations import Transformation
from .transformations import TransformationsNamespace


class Analysis:
    """High-level analysis API for notebook workflows."""

    def __init__(self, context: Context, *, client=None):
        self._context = context
        self._client = client
        self._transformations = TransformationsNamespace(self)
        self._cohorts = None
        self._describe = None
        self._tests = None
        self._models = None

    @property
    def context(self) -> Context:
        return self._context

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            return get_client()
        except Exception as exc:
            raise MipConfigurationError(
                "No platform-backend client is configured for this notebook environment."
            ) from exc

    def with_transformations(self, transformations: Sequence[Transformation]) -> Analysis:
        """Return a new Analysis bound to an updated context."""
        return Analysis(self._context.with_transformations(transformations), client=self._client)

    @property
    def transformations(self) -> TransformationsNamespace:
        return self._transformations

    @property
    def cohorts(self):
        if self._cohorts is None:
            from .cohorts import CohortsNamespace

            self._cohorts = CohortsNamespace(self)
        return self._cohorts

    @property
    def describe(self):
        if self._describe is None:
            from .describe import DescribeNamespace

            self._describe = DescribeNamespace(self)
        return self._describe

    @property
    def tests(self):
        if self._tests is None:
            from .tests import TestsNamespace

            self._tests = TestsNamespace(self)
        return self._tests

    @property
    def models(self):
        if self._models is None:
            from .models import ModelsNamespace

            self._models = ModelsNamespace(self)
        return self._models
