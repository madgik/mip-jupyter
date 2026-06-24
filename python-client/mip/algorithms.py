"""Backend algorithm catalog wrappers."""

from __future__ import annotations

from typing import Any
from typing import Mapping


class Algorithm:
    """One algorithm specification returned by the backend."""

    def __init__(self, data: Mapping[str, Any]):
        self._data = dict(data or {})
        self.name = self._data.get("name")
        self.label = self._data.get("label") or self.name
        self.type = self._data.get("type")

    def spec(self, client=None) -> dict[str, Any]:
        return dict(self._data)

    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "type": self.type,
            "desc": self._data.get("desc"),
        }


class AlgorithmRegistry:
    """Read-only registry backed by `/algorithms`."""

    def __init__(self, transport):
        self._transport = transport

    def list(self) -> list[Algorithm]:
        payload = self._transport.get("/specifications/algorithms")
        if isinstance(payload, dict):
            payload = payload.get("algorithms") or payload.get("items") or []
        if not isinstance(payload, list):
            return []
        return [Algorithm(item) for item in payload if isinstance(item, dict)]

    def search(self, text: str = "") -> list[Algorithm]:
        needle = str(text or "").lower()
        if not needle:
            return self.list()
        return [
            item
            for item in self.list()
            if needle in str(item.name or "").lower()
            or needle in str(item.label or "").lower()
            or needle in str(item.spec().get("desc") or "").lower()
        ]

    def preprocessing(self) -> list[Algorithm]:
        return self._by_types("preprocessing")

    def statistics(self) -> list[Algorithm]:
        return self._by_types("stat", "statistics")

    def models(self) -> list[Algorithm]:
        return self._by_types("model", "models")

    def _by_types(self, *texts: str) -> list[Algorithm]:
        needles = [text.lower() for text in texts]
        matches = []
        seen = set()
        for item in self.list():
            kind = str(item.type or "").lower()
            if not any(needle in kind for needle in needles):
                continue
            key = item.name or id(item)
            if key in seen:
                continue
            seen.add(key)
            matches.append(item)
        return matches

    def to_frame(self):
        from .display import to_frame

        return to_frame(self.list())

    def help(self) -> str:
        from .display import show_help

        return show_help("AlgorithmRegistry")
