# mip-jupyter

Jupyter and JupyterHub image assets plus the `mip` Python client for federated analysis via platform-backend.

## Repository Layout

- `Dockerfile.jupyter` - single-user Jupyter image that installs the client and ships notebooks
- `Dockerfile.jupyterhub` - JupyterHub image with JupyterLab, OAuth helpers, and the client
- `Welcome.ipynb` - getting-started notebook for the MVP `mip` API
- `feres_analysis.ipynb` - Feres stroke territory example notebook
- `python-client/mip/` - `mip` package source
- `python-client/tests/` - mocked unit tests
- `expected_library.md` - public API contract

## Local Notebook Setup

Use `uv` from the repository root:

```bash
uv sync
uv run mip-notebook
```

The notebook runner opens `feres_analysis.ipynb` on `127.0.0.1:8888` with token `dev`. It defaults `PLATFORM_BACKEND_URL` to `http://127.0.0.1:8080/services` unless `PLATFORM_BACKEND_URL` or `MIP_BASE_URL` is already set.

Open:

```text
http://127.0.0.1:8888/tree/feres_analysis.ipynb?token=dev
```

To open a different notebook:

```bash
MIP_NOTEBOOK=Welcome.ipynb uv run mip-notebook
```

## Install Without UV

```bash
cd python-client && poetry install
```

Or:

```bash
python3 -m pip install -e ./python-client
```

## Quick Start

```python
import mip
from mip.filters import F
from mip.preprocessing import MissingValuesHandler

client = mip.Client.from_env()
catalog = client.catalog()
dm = catalog.data_model("dementia")

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

histogram = pipeline.histogram(variable=mmse, bins=20)
histogram.summary()
```

See [`expected_library.md`](expected_library.md) and [`Welcome.ipynb`](Welcome.ipynb) for the full MVP API.

## Environment Variables

`Client.from_env()` reads:

- `PLATFORM_BACKEND_URL` or `MIP_BASE_URL` - platform-backend base URL, for example `http://platform-backend:8080/services`
- `PLATFORM_TOKEN` or `MIP_TOKEN` - bearer token for platform-backend
- `PLATFORM_BACKEND_TIMEOUT` - request timeout in seconds (default `30`)
- `PLATFORM_BACKEND_ALLOW_REDIRECTS` - set to `1` only when redirects should be followed

JupyterHub also injects `JUPYTERHUB_API_URL` and `JUPYTERHUB_API_TOKEN` for automatic token refresh.

Tests use mocked HTTP only and do not require live services.

## Tests

```bash
uv run python -m unittest discover -s python-client/tests -p "test_*.py"
uv run python python-client/verify_script.py
```

Without `uv`:

```bash
cd python-client && python3 -m unittest discover -s tests -p "test_*.py"
python3 python-client/verify_script.py
```

## Build Images

```bash
docker build \
  --build-arg JUPYTER_SCIPY_IMAGE=jupyter/scipy-notebook@sha256:<digest> \
  -f Dockerfile.jupyter -t mip-jupyter:dev .
docker build -f Dockerfile.jupyterhub -t mip-jupyterhub:dev .
```

Pin `JUPYTER_SCIPY_IMAGE` to a digest for reproducible builds.

## Development Notes

- Mock HTTP in tests; no live backend in unit tests
- Never commit real tokens
- Generated artifacts (`build/`, `*.egg-info/`, `__pycache__/`, `.venv/`) are gitignored
