# mip-jupyter

Jupyter and JupyterHub image assets plus a lightweight Python client for the Portal Backend API.

## Repository Layout

- `Dockerfile.jupyter`: single-user Jupyter image (installs local client and ships `Welcome.ipynb`).
- `Dockerfile.jupyterhub`: JupyterHub image (installs JupyterLab, `oauthenticator`, and local client).
- `sample_notebook.ipynb`: onboarding notebook copied into images.
- `python-client/portal_backend_client/`: Python package source.
- `python-client/tests/`: unit tests.

Generated directories such as `python-client/build/`, `*.egg-info/`, and `__pycache__/` are build artifacts.

## Python Client Quick Start

```bash
python3 -m pip install -e ./python-client
```

```python
from portal_backend_client import configure, Experiment

configure(base_url="http://localhost:8080/services", token="<bearer-token>")
experiments = Experiment.list(limit=10)
print(experiments)
```

Client defaults can be driven by environment variables:
- `PORTAL_BACKEND_URL` (default: `http://portalbackend:8080/services`)
- `PORTAL_TOKEN`
- `PORTAL_BACKEND_TIMEOUT` (default: `30`)
- `PORTAL_BACKEND_ALLOW_REDIRECTS` (default: `0`)

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
- Prefer adding regression tests alongside behavior changes in `portal_backend_client`.
- Never commit real tokens or credentials.
