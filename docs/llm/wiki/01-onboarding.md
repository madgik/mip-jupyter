# Onboarding — New MIP User

**Read when:** The user is new to MIP or asks what to do first in a notebook.

**Skip if:** The user is editing notebook infrastructure or the Python client (see `dev-contributor.md`).

## Goal

Connect to platform-backend, discover a data model, select datasets and variables, run a simple analysis.

## Steps

### 1. Initialize the client

```python
import mip

client = mip.Client.from_env()
catalog = client.catalog()
```

`Client.from_env()` reads `PLATFORM_BACKEND_URL` (or `MIP_BASE_URL`) and `MIP_TOKEN` (or `PLATFORM_TOKEN`). See `05-env-and-backend.md` for details.

### 2. Discover data models

```python
catalog.list()       # list of DataModel objects
catalog.tree()       # ASCII overview
dm = catalog.data_model("dementia")  # or another model name
dm.summary()
dm.tree(include_variables=True)
```

### 3. Select datasets and variables

```python
adni = dm.datasets["adni"]
age = dm.variables["age"]
mmse = dm.variables["mmse"]
```

Use `dm.variables.search("MMSE")` or `dm.datasets.search("adni")` to find codes.

Objects expose `.help()` for method hints. See `docs/how-to-choose.md` (workspace `docs/`) for a goal → API decision guide.

```python
dm.help()
dm.variables.to_frame()
pipeline.recommend_algorithms()
```

### 4. Create an analysis scope

```python
from mip.filters import F
from mip.preprocessing import MissingValuesHandler

analysis_set = mip.AnalysisSet(
    data_model=dm,
    datasets=[adni],
    variables=[age, mmse],
)

pipeline = mip.Pipeline(
    analysis_set=analysis_set,
    filters=F(age) >= 50,
    handle_missing=MissingValuesHandler(strategies={mmse: "mean"}),
)

result = pipeline.histogram(variable=mmse, bins=20)
result.summary()
```

## Runnable companion

Run cells in `workspace/Welcome.ipynb` for the full getting-started walkthrough.

## Rules

- No direct Exaflow calls — all HTTP goes through platform-backend.
- No `.table()` API — it does not exist.

**Next file:** `workspace/Welcome.ipynb` for hands-on practice, or `02-analysis-workflow.md` for pipeline details.
