# mip-jupyter

Jupyter and JupyterHub image assets plus a lightweight Python client for the Platform Backend API.

## Repository Layout

- `Dockerfile.jupyter`: single-user Jupyter image (installs local client and ships `Welcome.ipynb`).
- `Dockerfile.jupyterhub`: JupyterHub image (installs JupyterLab, `oauthenticator`, and local client).
- `sample_notebook.ipynb`: onboarding notebook copied into images.
- `python-client/mip/`: Python package source.
- `python-client/tests/`: unit tests.

Generated directories such as `python-client/build/`, `*.egg-info/`, and `__pycache__/` are build artifacts.

## Python Client Quick Start

```bash
python3 -m pip install -e ./python-client
```

Preferred notebook facade:

```python
from mip import (
    configure,
    metadata,
    algorithms,
    experiments,
    filters,
    FederatedLogisticRegression,
    FederatedLinearRegression,
    FederatedNaiveBayes,
)

configure(base_url="http://localhost:8080/services", token="<bearer-token>")
print(metadata.list())
print(algorithms.list())
print(experiments.list(limit=5))
print(metadata.describe("dementia:0.1"))
print(metadata.describe("dementia:0.1", include_variables=True, max_lines=120))
```

Direct class-level API is available from the same package:

```python
from mip import (
    configure,
    Experiment,
    FederatedLogisticRegression,
    FederatedLinearRegression,
    FederatedNaiveBayes,
)

configure(base_url="http://localhost:8080/services", token="<bearer-token>")
experiments = Experiment.list(limit=10)
print(experiments)
```

Client defaults can be driven by environment variables:
- `PLATFORM_BACKEND_URL` (default: `http://platform-backend:8080/services`)
- `PLATFORM_TOKEN` (preferred)
- `PORTAL_TOKEN`
- `PLATFORM_BACKEND_TIMEOUT` (default: `30`)
- `PLATFORM_BACKEND_ALLOW_REDIRECTS` (default: `0`)

## Run Tests

```bash
cd python-client && python3 -m unittest discover -s tests -p "test_*.py"
```

Optional (pytest-compatible discovery is configured):

```bash
python3 -m pytest python-client/tests -q
```

Smoke verification script:

```bash
python3 python-client/verify_script.py
```

## Build Images

```bash
docker build \
  --build-arg JUPYTER_SCIPY_IMAGE=jupyter/scipy-notebook@sha256:<digest> \
  -f Dockerfile.jupyter -t mip-jupyter:dev .
docker build -f Dockerfile.jupyterhub -t mip-jupyterhub:dev .
```

For reproducible builds, pin `JUPYTER_SCIPY_IMAGE` to a digest rather than a floating tag.

## Development Notes

- Keep API calls in tests mocked (`unittest.mock`); avoid live backend dependencies.
- Prefer adding regression tests alongside behavior changes in `python-client/mip`.
- Never commit real tokens or credentials.
