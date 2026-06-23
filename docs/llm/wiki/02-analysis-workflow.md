# Analysis Workflow

**Read when:** The user wants to build or extend a federated analysis notebook.

**Skip if:** The user only needs env configuration (`05-env-and-backend.md`) or MCP notebook edits (`04-jupyter-mcp.md`).

## Pattern

```text
Connect → Discover → Select → Transform → Analyze
```

## 1. Connect and discover

```python
import mip
from mip.filters import F
from mip.preprocessing import (
    CategoricalColumnCreator,
    MissingValuesHandler,
    OutlierWinsorizer,
)

client = mip.Client.from_env()
dm = client.catalog().data_model("dementia")
dataset = dm.datasets["adni"]
variables = [dm.variables["age"], dm.variables["mmse"]]
```

## 2. Define analysis scope

```python
analysis_set = mip.AnalysisSet(
    data_model=dm,
    datasets=[dataset],
    variables=variables,
)
```

## 3. Configure filters and preprocessing

```python
filters = (F(age) >= 50) & F(mmse).is_not_null()

missing = MissingValuesHandler(strategies={mmse: "mean"})
outliers = OutlierWinsorizer(strategies={mmse: "iqr"}, tails={mmse: "both"}, folds={mmse: 1.5})

creator = CategoricalColumnCreator(
    code="cognitive_profile",
    rules={"preserved": F(mmse) >= 27, "impaired": F(mmse) < 20},
    default_enumeration="unclassified",
)
```

## 4. Build pipeline and run algorithms

```python
pipeline = mip.Pipeline(
    analysis_set=analysis_set,
    filters=filters,
    handle_missing=missing,
    outlier_handling=outliers,
    new_columns=[creator],
)

pipeline.describe()
pipeline.histogram(variable=mmse, bins=20)
pipeline.t_test(variable=mmse, group_by=diagnosis, group_a="AD", group_b="CN")
pipeline.logistic_regression(x=[age, mmse], y=diagnosis, positive_class="AD")
```

## Execution order (fixed)

```text
AnalysisSet → filters → handle_missing → outlier_handling → new_columns → algorithm
```

## Execution modes

- Default: `mode="transient"` → `POST /experiments/transient`
- Persisted: `mode="persisted"` → `POST /experiments`

## Results

```python
result.summary()
result.raw
result.payload
```

Logistic regression also supports `result.to_sklearn()` and `result.feature_schema()`.

## Reference notebook

`workspace/examples/feres_analysis.ipynb` demonstrates stroke territory cohort analysis with `CategoricalColumnCreator`.

**Next file:** `workspace/examples/feres_analysis.ipynb` for a full example, or `03-mip-client-api.md` for API details.
