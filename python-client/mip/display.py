"""Notebook display helpers: help text, HTML cards, and tabular previews."""

from __future__ import annotations

from typing import Any
from typing import Iterable
from typing import Mapping
from typing import Sequence

from .labels import public_label

HELP_TEXT: dict[str, str] = {
    "Client": """\
Client help

Useful methods:
- client.catalog()       browse data models, datasets, and variables
- client.algorithms()    search available algorithms
- client.experiments()   list or run persisted experiments

Typical next step:
  catalog = client.catalog()
  catalog.summaries()""",
    "Catalog": """\
Catalog help

Useful methods:
- catalog.summaries()         compact list of data models
- catalog.tree()              ASCII overview of all models
- catalog.data_model("Dementia")  pick one model to explore
- catalog.list()              all DataModel objects

Typical next step:
  dm = catalog.data_model("Dementia")
  dm.summary()""",
    "DataModel": """\
DataModel help

Useful methods:
- dm.summary()                high-level counts and metadata
- dm.list_datasets()          dataset summaries as dicts
- dm.datasets.list()          Dataset objects
- dm.list_variables()         variable summaries as dicts
- dm.variables.search("Age")  find variables by name
- dm.variables.numerical()    numeric variables only
- dm.variables.categorical()  categorical variables only
- dm.tree()                   hierarchy view
- dm.variables.tree(group="Demographics")

Typical next step:
  age = dm.variables["Age"]
  age.summary()""",
    "Dataset": """\
Dataset help

Useful methods:
- dataset.summary()       label and variable count
- dataset.details()       label-safe metadata
- dataset.variables()     variables available in this dataset
- dataset.has_variable(v) check whether a variable is present

Typical next step:
  adni = dm.datasets["ADNI"]
  adni.variables()""",
    "DatasetCollection": """\
DatasetCollection help

Useful methods:
- dm.datasets.list()          all datasets
- dm.datasets.search("ADNI")  find datasets by name
- dm.datasets.to_frame()      tabular preview
- dm.datasets["ADNI"]         pick one dataset

Typical next step:
  adni = dm.datasets["ADNI"]""",
    "Variable": """\
Variable help

Useful methods:
- variable.summary()    label, type, numerical/categorical flags
- variable.details()    label-safe metadata and categories
- variable.categories() allowed category labels (if categorical)

Typical next step:
  age = dm.variables["Age"]
  age.summary()""",
    "VariableCollection": """\
VariableCollection help

Useful methods:
- dm.variables.search("Age")     find by label
- dm.variables.numerical()       numeric variables only
- dm.variables.categorical()     categorical variables only
- dm.variables.to_frame()        tabular preview
- dm.variables.tree(group="Demographics")   group hierarchy
- dm.variables["Age"]           pick one variable

Typical next step:
  age = dm.variables["Age"]""",
    "AnalysisSet": """\
AnalysisSet help

Useful methods:
- analysis_set.summary()   selected model, datasets, variables
- analysis_set.explain()     inputdata payload preview
- analysis_set.histogram()   quick one-off histogram (via Pipeline)

Typical next step:
  pipeline = mip.Pipeline(analysis_set=analysis_set, filters=...)
  pipeline.explain()""",
    "Pipeline": """\
Pipeline help

Useful methods:
- pipeline.explain()              full request preview
- pipeline.summary()              analysis set + filters + preprocessing
- pipeline.available_algorithms() list callable algorithm methods
- pipeline.recommend_algorithms() suggested next steps
- pipeline.describe()             summary statistics
- pipeline.histogram(variable=...) distribution plot data
- pipeline.pearson_correlation(x=..., y=...)
- pipeline.logistic_regression(x=[...], y=..., positive_class=...)

Typical next step:
  pipeline.recommend_algorithms()
  result = pipeline.histogram(variable=mmse, bins=20)""",
    "Result": """\
Result help

Useful methods:
- result.summary()   backend result payload (same as .raw)
- result.raw         raw result dict or value
- result.payload     full experiment response
- result.plot()      matplotlib chart (histogram results only)

Typical next step:
  result.summary()""",
    "ModelResult": """\
ModelResult help

Useful methods:
- result.summary()      backend result payload
- result.raw            raw result dict
- result.payload        full experiment response
- result.feature_schema()  feature names from logistic regression
- result.to_sklearn()   export as sklearn classifier (logistic only)

Typical next step:
  result.summary()""",
    "AlgorithmRegistry": """\
AlgorithmRegistry help

Useful methods:
- client.algorithms().list()          all algorithms
- client.algorithms().search("text")  find by name or description
- client.algorithms().to_frame()      tabular preview
- client.algorithms().statistics()    statistical algorithms
- client.algorithms().models()        modelling algorithms

Typical next step:
  client.algorithms().search("logistic")""",
}


def escape_html(text: Any) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_object_card(
    title: str,
    fields: Mapping[str, Any],
    methods: Sequence[str] | None = None,
) -> str:
    """Render a compact HTML card for JupyterLab object display."""
    rows = "".join(
        f"<tr><th>{escape_html(key)}</th><td>{escape_html(value)}</td></tr>"
        for key, value in fields.items()
    )
    methods_html = ""
    if methods:
        items = "".join(f"<li><code>{escape_html(item)}</code></li>" for item in methods)
        methods_html = f"<p><strong>Useful methods</strong></p><ul>{items}</ul>"
    return (
        f'<div style="font-family:monospace;font-size:13px;line-height:1.4">'
        f"<p><strong>{escape_html(title)}</strong></p>"
        f"<table>{rows}</table>{methods_html}</div>"
    )


def format_help(kind: str) -> str:
    try:
        return HELP_TEXT[kind]
    except KeyError as exc:
        raise ValueError(f"No help text registered for {kind!r}") from exc


class HelpText:
    """Notebook-friendly help text returned by object .help() methods."""

    def __init__(self, text: str):
        self._text = text

    def __str__(self) -> str:
        return self._text

    def _repr_html_(self) -> str:
        escaped = escape_html(self._text)
        return f"<pre style=\"white-space:pre-wrap\">{escaped}</pre>"

    def _repr_pretty_(self, p, cycle) -> None:
        if cycle:
            p.text("HelpText(...)")
            return
        p.text(self._text)


def show_help(kind: str) -> HelpText:
    return HelpText(format_help(kind))


def _summary_row(item: Any) -> dict[str, Any]:
    if hasattr(item, "summary") and callable(item.summary):
        summary = item.summary()
        if isinstance(summary, dict):
            return dict(summary)
    if isinstance(item, Mapping):
        return dict(item)
    return {"value": str(item)}


def to_frame(items: Iterable[Any]):
    """Convert variables, datasets, algorithms, or summary dicts to a DataFrame."""
    import pandas as pd

    rows = [_summary_row(item) for item in items]
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def recommend_pipeline_steps(variables: Sequence[Any]) -> str:
    """Suggest pipeline methods based on selected variable types."""
    lines = ["Based on your selected variables:"]
    numerical: list[Any] = []
    categorical: list[Any] = []

    for variable in variables:
        label = public_label(variable)
        is_num = getattr(variable, "is_numerical", lambda: False)()
        is_cat = getattr(variable, "is_categorical", lambda: False)()
        if is_num:
            kind = "numerical"
            numerical.append(variable)
        elif is_cat:
            kind = "categorical"
            categorical.append(variable)
        else:
            kind = "unknown"
        lines.append(f"- {label}: {kind}")

    lines.append("")
    lines.append("Possible next steps:")
    lines.append("- pipeline.describe()")
    lines.append("- pipeline.explain()")
    lines.append("- pipeline.available_algorithms()")

    if numerical:
        first = public_label(numerical[0])
        lines.append(f'- pipeline.histogram(variable=variables["{first}"])')
    if len(numerical) >= 2:
        x = public_label(numerical[0])
        y = public_label(numerical[1])
        lines.append(f'- pipeline.pearson_correlation(x=variables["{x}"], y=variables["{y}"])')
    if categorical and numerical:
        xs = ", ".join(f'variables["{public_label(item)}"]' for item in numerical[:2])
        y = public_label(categorical[0])
        lines.append(f'- pipeline.logistic_regression(x=[{xs}], y=variables["{y}"], positive_class=...)')
    elif len(categorical) >= 2:
        x = public_label(categorical[0])
        y = public_label(categorical[1])
        lines.append(f'- pipeline.chi_square_test(x=variables["{x}"], y=variables["{y}"])')

    return "\n".join(lines)
