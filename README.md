# mip-jupyter

Jupyter and JupyterHub image assets plus the `mip` Python client for federated analysis via platform-backend.

## Repository Layout

- `Dockerfile.jupyter` — single-user Jupyter image (installs client, ships `Welcome.ipynb`)
- `Dockerfile.jupyterhub` — JupyterHub image (JupyterLab, OAuth, client)
- `sample_notebook.ipynb` — onboarding notebook copied into images
- `python-client/mip/` — `mip` package source
- `python-client/tests/` — unit tests
- `expected_library.md` — public API contract

## Install

```bash
cd python-client && poetry install
```

Or:

```bash
python3 -m pip install -e ./python-client
```

## Quick Start

```python
from mip import configure, catalog, Context, Analysis

configure(base_url="http://localhost:8080/services", token="<bearer-token>")

# Discover data models and datasets
catalog.models().to_dataframe()
catalog.datasets("stroke:1.0").to_dataframe()
catalog.visualize("stroke:1.0", include_variables=True)

# Run analysis
context = Context(data_model="stroke:1.0", datasets=["ssrdataset_harmonized"])
analysis = Analysis(context)

summary = analysis.describe.numeric(variables=["age"])
summary.to_dataframe()
```

See [`expected_library.md`](expected_library.md) for the full API (transformations, tests, models, reports).

## Environment Variables

- `PLATFORM_BACKEND_URL` — default `http://platform-backend:8080/services`
- `PLATFORM_TOKEN` / `PORTAL_TOKEN` — bearer token
- `PLATFORM_BACKEND_TIMEOUT` — default `30`
- `PLATFORM_BACKEND_ALLOW_REDIRECTS` — default `0`

## Tests

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
