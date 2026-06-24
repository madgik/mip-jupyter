# MIP Python Client — Quickstart

The `mip` package is pre-installed in this Jupyter environment. Use it to run federated analysis through platform-backend.

## Connect

```python
import mip

client = mip.Client.from_env()
catalog = client.catalog()
```

`Client.from_env()` reads:

- `PLATFORM_BACKEND_URL` or `MIP_BASE_URL` — backend base URL (for example `http://platform-backend:8080/services`)
- `MIP_TOKEN` or `PLATFORM_TOKEN` — bearer token for platform-backend

## Discover data

```python
catalog.list()
catalog.tree()
dm = catalog.data_model("dementia")
dm.summary()
```

## Run a simple analysis

```python
from mip.filters import F
from mip.preprocessing import MissingValuesHandler

adni = dm.datasets["adni"]
age = dm.variables["age"]
mmse = dm.variables["mmse"]

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

## Next steps

- Open `Welcome.ipynb` for a guided walkthrough.
- See [How to choose the right API call](how-to-choose.md) when you are unsure which method to use.
- See `examples/feres_analysis.ipynb` for a stroke-territory analysis.
- See [API reference](api-reference.md) for the full cheat sheet.
- Save your own notebooks under `scratch/`.
