# Onboarding — New MIP User

**Read when:** The user is new to MIP or asks what to do first in a notebook.

**Skip if:** The user is editing notebook infrastructure or the Python client (see `dev-contributor.md`).

## Goal

Connect to the MIP platform, discover a data model, select datasets and variables, run a simple analysis.

## Steps

### 1. Initialize the client

```python
import mip

client = mip.Client.from_env()
catalog = client.catalog()
```

`Client.from_env()` uses the platform connection configured when the user opens Jupyter from the MIP portal. See `05-env-and-backend.md` for operator and developer env details — do not quote env var names to end users unless they ask about local development setup.

### 2. Discover data models

```python
catalog.list()       # list of DataModel objects
catalog.tree()       # ASCII overview
dm = catalog.data_model("Dementia")  # select by label
dm.summary()
dm.tree(include_variables=True)
```

### 3. Select datasets and variables

```python
adni = dm.datasets["ADNI"]
age = dm.variables["Age"]
mmse = dm.variables["MMSE"]
```

Use `dm.variables.search("MMSE")` or `dm.datasets.search("ADNI")` to find items by label or description.

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

- No direct calls to internal execution services — use the `mip` client and platform APIs only.
- No `.table()` API — it does not exist.
- Select and read **labels** only; internal codes are never shown in notebook code.

**Next file:** `workspace/Welcome.ipynb` for hands-on practice, or `02-analysis-workflow.md` for pipeline details.
