# MIP Client API Cheat Sheet

**Read when:** You need API syntax for filters, preprocessing, pipeline methods, or results.

**Skip if:** `01-onboarding.md` or `02-analysis-workflow.md` already covers the task. Do not read [expected_library.md](../../../expected_library.md) unless this page is insufficient.

## Design rules

- Thin client over platform-backend — no direct Exaflow calls.
- Entry points: `mip.Client`, `mip.AnalysisSet`, `mip.Pipeline`.
- No `.table()` API.

## Imports

```python
import mip
from mip.filters import F
from mip.preprocessing import CategoricalColumnCreator, MissingValuesHandler, OutlierWinsorizer
```

## Client and catalog

```python
client = mip.Client.from_env()
catalog = client.catalog()
dm = catalog.data_model("code", version="x.y")  # version optional
dm.datasets["name"]
dm.variables["code"]
dm.variables.search("text")
```

## Filters

```python
(F(age) >= 50) & F(mmse).is_not_null()
F(diagnosis).isin(["AD", "CN"])
F(mmse).between(20, 26)
expr1 | expr2
~F(x).isin([...])  # rewrites to not_in
```

String-match operators (`contains`, `starts_with`, `ends_with`) may not be accepted by the backend validator.

## Preprocessing

```python
MissingValuesHandler(strategies={age: "median", mmse: "mean"})
OutlierWinsorizer(strategies={mmse: "iqr"}, tails={mmse: "both"}, folds={mmse: 1.5})
CategoricalColumnCreator(code="cohort", rules={...}, default_enumeration="other")
```

Use `creator.variable` for the derived column in downstream algorithms.

## Pipeline algorithms

`describe`, `histogram`, `t_test`, `pearson_correlation`, `chi_square_test`, `logistic_regression`

```python
pipeline = mip.Pipeline(analysis_set=..., filters=..., handle_missing=...)
pipeline.histogram(variable=mmse, bins=20)
pipeline.logistic_regression(x=[age, sex], y=diagnosis, positive_class="AD")
```

## Algorithm and experiment registries

```python
client.algorithms().list()
client.algorithms().search("logistic")
client.experiments().list()
```

## Results

```python
result.summary()
result.raw
result.payload
logreg.to_sklearn()  # logistic regression only
```

## Full contract

See [expected_library.md](../../../expected_library.md) for module layout, payload shapes, and compliance details.

**Next file:** `python-client/mip/` source only when fixing client behavior; otherwise return to the user's notebook task.
