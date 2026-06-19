# Repository Guidelines

## Project Structure & Module Organization
This repository has two deliverables: container images and a Python client.
- `Dockerfile.jupyter` builds the single-user notebook image and ships `Welcome.ipynb` and `feres_analysis.ipynb`.
- `Dockerfile.jupyterhub` builds the hub-side image with JupyterLab, OAuth helpers, and the local client package.
- `Welcome.ipynb` is the getting-started notebook copied to `/opt/portal-notebooks/Welcome.ipynb`.
- `feres_analysis.ipynb` is the Feres stroke territory example notebook.
- `python-client/mip/` contains the library modules (`client.py`, `catalog.py`, `datamodel.py`, `analysis.py`, `pipeline.py`, `filters.py`, `preprocessing.py`, `algorithms.py`, `results.py`, `sklearn.py`, `transport.py`, `exceptions.py`).
- `python-client/tests/` holds unit tests; `python-client/conftest.py` keeps imports stable during test discovery.
- `python-client/pyproject.toml` defines Poetry package metadata and dependencies.
- `expected_library.md` documents the public API contract exercised by `Welcome.ipynb`.
Do not hand-edit generated artifacts in `build/`, `*.egg-info/`, or `__pycache__/`.

## Build, Test, and Development Commands
- `cd python-client && poetry install`: install the client and dev dependencies with Poetry.
- `python3 -m pip install -e ./python-client`: install the client in editable mode with pip.
- `cd python-client && python3 -m unittest discover -s tests -p "test_*.py"`: run the main unit test suite.
- `python3 -m pytest python-client/tests -q`: run tests with pytest (supported via `conftest.py`).
- `python3 python-client/verify_script.py`: quick mocked smoke check of catalog and pipeline flows.
- `client.catalog().data_model("code", version="x.y")` discovers data models before creating an `AnalysisSet`.
- `docker build --build-arg JUPYTER_SCIPY_IMAGE=jupyter/scipy-notebook@sha256:<digest> -f Dockerfile.jupyter -t mip-jupyter:dev .`: build notebook image reproducibly.
- `docker build -f Dockerfile.jupyterhub -t mip-jupyterhub:dev .`: build hub image.

## Coding Style & Naming Conventions
Use Python 3 with PEP 8 defaults: 4-space indentation, readable line lengths, and docstrings for public APIs.
- Modules/functions/variables: `snake_case`
- Classes: `PascalCase`
- Environment variables: `UPPER_SNAKE_CASE`
Prefer explicit error messages and deterministic behavior (no hidden network side effects in tests).

## Testing Guidelines
Tests are `unittest`-based and rely on `unittest.mock` to patch `requests.Session` methods.
- Name files `test_*.py` and test methods `test_<behavior>`.
- Keep tests isolated from real services; no live HTTP calls.
- Add a regression test with every behavior fix in `mip`.

## Commit & Pull Request Guidelines
Local `.git` history is not included in this checkout, so follow a consistent convention:
- Use concise, imperative commit subjects (optionally Conventional Commits), e.g. `fix(client): handle expired token refresh`.
- Keep commits focused on one logical change.
- PRs should include: what changed, why, test commands run, and any config/env impacts.
- For notebook or UX-facing changes, include screenshots or brief output snippets.

## Security & Configuration Tips
Never commit real credentials or tokens. Use environment variables such as `PLATFORM_BACKEND_URL`, `PLATFORM_TOKEN`, `MIP_TOKEN`, `PLATFORM_BACKEND_TIMEOUT`, and `PLATFORM_BACKEND_ALLOW_REDIRECTS` for runtime configuration.
