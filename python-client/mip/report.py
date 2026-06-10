"""Notebook report assembly."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import List
from typing import Sequence

from .results import ResultTable


@dataclass
class ReportSection:
    title: str
    result: ResultTable | Any


@dataclass
class Report:
    title: str
    sections: Sequence[ReportSection]

    def display(self) -> None:
        try:
            from IPython.display import HTML
            from IPython.display import display
        except ImportError:
            self._print_fallback()
            return

        display(HTML(f"<h1>{_escape(self.title)}</h1>"))
        for section in self.sections:
            display(HTML(f"<h2>{_escape(section.title)}</h2>"))
            result = section.result
            if hasattr(result, "to_dataframe"):
                display(result.to_dataframe())
            elif hasattr(result, "summary") and callable(result.summary):
                display(result.summary().to_dataframe())
            else:
                display(result)

    def _print_fallback(self) -> None:
        print(self.title)
        for section in self.sections:
            print(f"\n{section.title}")
            result = section.result
            if hasattr(result, "to_dataframe"):
                print(result.to_dataframe())
            elif hasattr(result, "summary") and callable(result.summary):
                print(result.summary().to_dataframe())
            else:
                print(result)


def _escape(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
