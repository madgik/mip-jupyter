"""Lightweight API discovery helpers for notebook users.

Jupyter autocomplete (Tab) is often unreliable in embedded/iframe setups.
These helpers give a deterministic way to find classes/methods and their
signatures/docstrings.
"""

from __future__ import annotations

import inspect
import re
from dataclasses import dataclass
from typing import Any, Iterable, List, Optional


@dataclass(frozen=True)
class ApiItem:
    """A single discoverable API item."""

    path: str
    kind: str
    signature: str
    doc: str


def _safe_signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception:
        return "()"


def _first_line_doc(obj: Any) -> str:
    doc = inspect.getdoc(obj) or ""
    return (doc.strip().splitlines() or [""])[0]


def iter_members(obj: Any, *, include_private: bool = False) -> Iterable[tuple[str, Any]]:
    """Iterate members of an object with basic filtering."""
    for name, member in inspect.getmembers(obj):
        if not include_private and name.startswith("_"):
            continue
        yield name, member


def show_api(obj: Any, *, include_private: bool = False, max_items: int = 200) -> List[ApiItem]:
    """Return discoverable members of `obj`.

    Intended for notebooks:
        from platform_backend_client import Experiment, show_api
        show_api(Experiment)
    """
    items: List[ApiItem] = []
    base = getattr(obj, "__name__", obj.__class__.__name__)

    for name, member in iter_members(obj, include_private=include_private):
        if len(items) >= int(max_items):
            break
        kind = "attribute"
        if inspect.isclass(member):
            kind = "class"
        elif inspect.isfunction(member) or inspect.ismethod(member) or callable(member):
            kind = "callable"
        items.append(
            ApiItem(
                path=f"{base}.{name}",
                kind=kind,
                signature=_safe_signature(member) if kind in ("callable", "class") else "",
                doc=_first_line_doc(member),
            )
        )
    return items


def search_api(
    obj: Any,
    query: str,
    *,
    include_private: bool = False,
    regex: bool = False,
    max_items: int = 200,
) -> List[ApiItem]:
    """Search members of `obj` by name/doc.

    Args:
        obj: A module/class/instance to search (e.g., Experiment).
        query: Substring or regex pattern.
        include_private: Include members starting with "_".
        regex: Treat `query` as regex if True.
        max_items: Cap on returned results.
    """
    if not isinstance(query, str) or not query.strip():
        return []

    q = query.strip()
    pattern: Optional[re.Pattern[str]] = None
    if regex:
        pattern = re.compile(q, re.IGNORECASE)
    q_lower = q.lower()

    hits: List[ApiItem] = []
    for item in show_api(obj, include_private=include_private, max_items=10_000):
        hay = f"{item.path}\n{item.doc}".lower()
        ok = False
        if pattern is not None:
            ok = bool(pattern.search(f"{item.path}\n{item.doc}"))
        else:
            ok = q_lower in hay
        if ok:
            hits.append(item)
            if len(hits) >= int(max_items):
                break
    return hits


def as_table(items: List[ApiItem]):
    """Render ApiItems as a pandas DataFrame if pandas is available."""
    try:
        import pandas as pd  # type: ignore
    except Exception:
        return items
    return pd.DataFrame([i.__dict__ for i in items], columns=["path", "kind", "signature", "doc"])

