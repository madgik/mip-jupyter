# MIP Client API Cheat Sheet

**Read when:** You need API syntax for filters, preprocessing, pipeline methods, or results.

**Skip if:** `01-onboarding.md` or `02-analysis-workflow.md` already covers the task. Do not read [expected_library.md](../../../expected_library.md) unless this page is insufficient.

## Design rules

- Thin client over platform-backend — no direct Exaflow calls.
- Entry points: `mip.Client`, `mip.AnalysisSet`, `mip.Pipeline`.
- No `.table()` API.
- Public identity is **label**, not internal code. Selection, summaries, trees, and explain previews show labels only.

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
dm = catalog.data_model("Dementia", version="0.1")  # version optional
dm.datasets["ADNI"]
dm.variables["Age"]
dm.variables.search("MMSE")
```

## Discoverability

```python
dm.help()
pipeline.help()
dm.variables.to_frame()
mip.to_frame(dm.variables.search("age"))
pipeline.recommend_algorithms()
variable.details()   # label-safe metadata (replaces metadata())
variable.categories()  # human-readable enumeration labels
```

User guide: `docs/user/how-to-choose.md`.

## Filters

```python
(F(age) >= 50) & F(mmse).is_not_null()
F(diagnosis).isin(["Alzheimer's disease", "CN"])  # enumeration labels
F(mmse).between(20, 26)
expr1 | expr2
~F(x).isin([...])  # rewrites to not_in
```

String-match operators (`contains`, `starts_with`, `ends_with`) may not be accepted by the backend validator.

## Preprocessing

```python
MissingValuesHandler(strategies={age: "median", mmse: "mean"})
OutlierWinsorizer(strategies={mmse: "iqr"}, tails={mmse: "both"}, folds={mmse: 1.5})
CategoricalColumnCreator(label="Cognitive profile", rules={...}, default_enumeration="Other")
```

Use `creator.variable` for the derived column in downstream algorithms.

## Pipeline algorithms

**30** typed methods on `mip.Pipeline`. Full catalog, signatures, and result keys: **`07-pipeline-algorithms.md`**. Runnable smoke test: `workspace/examples/algorithm_examples.py`.

```python
pipeline.available_algorithms()
client.algorithms().list()
```

## Pipeline algorithms (syntax)

```python
pipeline = mip.Pipeline(analysis_set=..., filters=..., handle_missing=..., new_columns=[creator])
pipeline.histogram(variable=mmse, bins=20)
pipeline.logistic_regression(x=[age, sex], y=diagnosis, positive_class="AD")
```

## Result.summary() shapes

| Algorithm | Keys |
|-----------|------|
| Describe | `featurewise[].data.mean`, `.std`, `.q2`, `.num_dtps` |
| Histogram | `histogram[0].bins`, `histogram[0].counts` |
| T-test | `t_stat`, `df`, `p`, `mean_diff`, `ci_lower`, `ci_upper`, `cohens_d` |
| Chi-square | `chi2`, `p_value`, `dof` |
| Logistic | `indep_vars`, `summary.coefficients`, `summary.pvalues`, `summary.lower_ci`, `summary.upper_ci` |

## Pipeline pitfalls

- No `Pipeline.run()`.
- `new_columns` takes creators; algorithms take `creator.variable`.
- Enumeration filter values are often codes (`"1"`, `"0"`), not display labels.

## Algorithm and experiment registries

```python
client.algorithms().list()
client.algorithms().search("logistic")
client.experiments().list()
```

`Algorithm.summary()` returns `{label, description, type}` only (no backend name).

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
