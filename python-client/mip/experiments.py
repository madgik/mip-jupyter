"""Experiment lifecycle helpers for notebook users."""

from __future__ import annotations

from typing import Optional

from .experiment import Experiment


def list(limit: int = 10, offset: int = 0):  # noqa: A001 - public API follows notebook convention
    """List experiments with pagination controls."""
    return Experiment.list(limit=limit, offset=offset)


def get(uuid: str) -> Experiment:
    """Get a single experiment by UUID."""
    return Experiment.get(uuid)


def create(
    name: str,
    algorithm_name: str,
    data_model: str,
    datasets: list,
    x: Optional[list] = None,
    y: Optional[list] = None,
    filters: Optional[dict] = None,
    parameters: Optional[dict] = None,
    preprocessing: Optional[dict] = None,
    mip_version: Optional[str] = None,
) -> Experiment:
    """Create a persisted experiment."""
    return Experiment.create(
        name=name,
        algorithm_name=algorithm_name,
        data_model=data_model,
        datasets=datasets,
        x=x,
        y=y,
        filters=filters,
        parameters=parameters,
        preprocessing=preprocessing,
        mip_version=mip_version,
    )


def run_transient(
    name: str,
    algorithm_name: str,
    data_model: str,
    datasets: list,
    x: Optional[list] = None,
    y: Optional[list] = None,
    filters: Optional[dict] = None,
    parameters: Optional[dict] = None,
    preprocessing: Optional[dict] = None,
    mip_version: Optional[str] = None,
    raise_on_failure: bool = True,
) -> Experiment:
    """Run a synchronous transient experiment (not persisted)."""
    return Experiment.run_transient(
        name=name,
        algorithm_name=algorithm_name,
        data_model=data_model,
        datasets=datasets,
        x=x,
        y=y,
        filters=filters,
        parameters=parameters,
        preprocessing=preprocessing,
        mip_version=mip_version,
        raise_on_failure=raise_on_failure,
    )
