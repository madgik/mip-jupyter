# MIP Jupyter Expected Library

Contract for the notebook-side `mip` library built in `mip-jupyter` and consumed inside Jupyter/JupyterHub.

## Design Rules

- The Python library is a thin client over `platform-backend`.
- Notebook code calls `platform-backend` only, not Exaflow directly.
- Data model discovery comes from backend data-model DTOs.
- Algorithm execution defaults to `/experiments/transient`; persisted execution uses `/experiments`.
- Search/list APIs return native Python lists.
- No `.table()` API exists.


## MVP Compliance Review

| MVP item | Implementation status |
|----------|-----------------------|
| Thin client over platform-backend | Implemented through internal `Transport`; no direct Exaflow calls. |
| Public entry points | `mip.Client`, `mip.AnalysisSet`, `mip.Pipeline`. |
| Public DSL/builders | `mip.filters.F`, `mip.preprocessing.MissingValuesHandler`, `mip.preprocessing.OutlierWinsorizer`, `mip.preprocessing.CategoricalColumnCreator`. |
| Derived variables | `mip.derived.DerivedVariable` exposed via `CategoricalColumnCreator.variable`. |
| Catalog objects | `Catalog`, `DataModel`, `VariableCollection`, `DatasetCollection`, `Variable`, `Dataset`. |
| Native list search/list results | `Catalog` search methods and collection `.search()` / `.to_list()` return `list`. |
| No old table API | No `.table()` method; old `ResultTable` API is removed. |
| AnalysisSet scope | Holds only selected data model, datasets, and variables. |
| Fixed Pipeline flow | Selection -> filters -> missing handling -> outlier handling -> new_columns -> algorithm. |
| Experiment payload | `analysis: AnalysisRequestDTO` with ordered `preprocessing` array and `inputdata.variables`. |
| Algorithm methods | `describe`, `histogram`, `t_test`, `pearson_correlation`, `chi_square_test`, `logistic_regression`. |
| Execution endpoints | `mode="transient"` posts `/experiments/transient`; `mode="persisted"` posts `/experiments`. |
| Preprocessing shape | Ordered preprocessing steps; strategy dictionaries keyed by variable code. |
| Results | `Result` and `ModelResult` expose `summary()`, `raw`, and `payload`; no enrichment APIs. |
| sklearn export | Implemented in `mip.sklearn` and exposed via `ModelResult.to_sklearn()`. |

## Module Layout

```text
mip/
  __init__.py
  client.py
  catalog.py
  datamodel.py
  data_model.py      # compatibility import for DataModel only
  variables.py
  datasets.py
  filters.py
  preprocessing.py
  derived.py
  request_builder.py
  analysis.py
  pipeline.py
  algorithms.py
  results.py
  sklearn.py
  transport.py
  metadata_tree.py
  exceptions.py
  errors.py          # compatibility aliases for exception imports only
```

`workspace/Welcome.ipynb` is the runnable companion to this contract.

## Public API

```python
import mip
from mip.filters import F
from mip.preprocessing import CategoricalColumnCreator, MissingValuesHandler, OutlierWinsorizer

client = mip.Client.from_env()
catalog = client.catalog()
algorithms = client.algorithms()
experiments = client.experiments()
```

Runnable companion notebook: `workspace/Welcome.ipynb`.

`Client.from_env()` reads:

```text
PLATFORM_BACKEND_URL or MIP_BASE_URL
PLATFORM_TOKEN or MIP_TOKEN
PLATFORM_BACKEND_TIMEOUT
PLATFORM_BACKEND_ALLOW_REDIRECTS
```

## Catalog Discovery

```python
catalog.list()
catalog.summaries()
catalog.tree()

dm = catalog.data_model("dementia")
dm.summary()
dm.list_datasets()
dm.datasets.list()
dm.list_groups()
dm.tree(include_variables=True)
dm.tree(group="clinical", include_variables=True)
dm.variables.tree(group="cognitive")
dm.variables.list()
dm.variables.search("MMSE")
dm.datasets.search("adni")
```

`catalog.list()` and `catalog.data_models()` return the same native list of `DataModel` objects. `catalog.tree()` renders an ASCII overview of all authorized models. Within a model, `datasets.list()` and `variables.list()` return flat lists for selection. `dm.tree()` and `dm.variables.tree()` render the backend group hierarchy; pass `group="clinical"` (code or label) to start from a specific group subtree. Use `dm.list_groups()` to discover available group codes.

## Analysis Set

```python
analysis_set = mip.AnalysisSet(
    data_model=dm,
    datasets=[adni],
    variables=[age, mmse],
)

analysis_set.summary()
analysis_set.explain()
analysis_set.histogram(variable=mmse, bins=20)
```

`AnalysisSet` only represents selected data model, datasets, and variables.

## Filters

```python
expr = (F(age) >= 50) & F(mmse).is_not_null()
expr.explain()
```

Supported operators and helpers:

```python
F(age) == 50
F(age) != 50
F(age) > 50
F(age) >= 50
F(age) < 80
F(age) <= 80
F(mmse).is_null()
F(mmse).is_not_null()
F(diagnosis).isin(["AD", "CN"])
F(diagnosis).not_in(["AD", "CN"])
F(mmse).between(20, 26)
F(mmse).not_between(20, 26)
expr1 & expr2
expr1 | expr2
~expr
```

`F.contains()`, `F.starts_with()`, and `F.ends_with()` serialize to the same operator names, but Exaflow currently accepts only the operators listed in its filter validator (`between`/`not_between` are supported; string-match operators are not yet).

`~expr` rewrites to Exaflow-supported operators (for example `~F(x).isin([...])` becomes `not_in`). Exaflow accepts only `AND` and `OR` group conditions.

## Preprocessing

```python
missing = MissingValuesHandler(
    strategies={age: "median", mmse: "mean"},
)

outliers = OutlierWinsorizer(
    strategies={mmse: "iqr"},
    tails={mmse: "both"},
    folds={mmse: 1.5},
)
```

Variable-object keys serialize to `variable.code`; string keys pass through unchanged.

`CategoricalColumnCreator` builds a derived categorical column from filter rules:

```python
creator = CategoricalColumnCreator(
    code="cognitive_profile",
    rules={
        "preserved": (F(mmse) >= 27) & (F(cdr) == 0),
        "severe_impairment": F(mmse) < 20,
    },
    default_enumeration="unclassified",
)

derived = creator.variable
derived.code
derived.categories()
derived.metadata()
```

The creator serializes to the `categorical_column_creator` preprocessing step with `strategy="filter_rules"`.

## Pipeline Execution

```python
pipeline = mip.Pipeline(
    analysis_set=analysis_set,
    filters=(F(age) >= 50) & F(mmse).is_not_null(),
    handle_missing=missing,
    outlier_handling=outliers,
    new_columns=[creator],
)

pipeline.describe()
pipeline.histogram(variable=mmse, bins=20)
pipeline.t_test(variable=mmse, group_by=diagnosis, group_a="AD", group_b="CN")
pipeline.pearson_correlation(x=mmse, y=cdr)
pipeline.chi_square_test(x=sex, y=diagnosis)
logreg = pipeline.logistic_regression(
    x=[age, sex, mmse, cdr, apoe4],
    y=diagnosis,
    positive_class="AD",
)
```

Execution order is fixed:

```text
AnalysisSet selection -> filters -> handle_missing -> outlier_handling -> new_columns -> algorithm
```

Experiment requests use:

```python
{
  "name": "...",
  "analysis": {
    "inputdata": {
      "data_model": "...",
      "datasets": ["..."],
      "validation_datasets": null,
      "filters": {...},
      "variables": ["..."],  # raw source variables only
    },
    "preprocessing": [
      {"name": "missing_values_handler", "parameters": {...}},
      {"name": "categorical_column_creator", "parameters": {...}},
    ],
    "algorithm": {
      "name": "...",
      "x": ["..."],
      "y": ["..."],
      "parameters": {...},
    },
  },
}
```


## Algorithm Registry

```python
registry = client.algorithms()
registry.list()
registry.search("logistic")
registry.preprocessing()
registry.statistics()
registry.models()
```

Each returned `Algorithm` exposes `.spec()` for the backend DTO and `.summary()` for a compact readable view.

## Experiment Registry

```python
experiments = client.experiments()
experiments.list()
experiments.get("experiment-id")
experiments.delete("experiment-id")
```

The experiment registry is for persisted experiment management. Pipeline execution remains the primary analysis API.

## Experiment Modes

All `AnalysisSet` and `Pipeline` execution methods default to transient execution:

```python
pipeline.histogram(variable=mmse)                  # POST /experiments/transient
pipeline.histogram(variable=mmse, mode="persisted") # POST /experiments
```

## Results

```python
result.summary()
result.raw
result.payload
```

Histogram results may support `.plot()`. Unsupported plotting raises `UnsupportedOperationError`.

Logistic regression results expose:

```python
logreg.feature_schema()
sklearn_model = logreg.to_sklearn()
sklearn_model.feature_names_in_
sklearn_model.predict(X_preprocessed)
sklearn_model.predict_proba(X_preprocessed)
```

Local prediction requires a user-preprocessed pandas DataFrame whose columns match `sklearn_model.feature_names_in_` exactly.
