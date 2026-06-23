# Release process

## Versioning

- `python-client/` (`mip` package) carries the client library version in `pyproject.toml`.
- Container images are tagged separately (for example `hbpmip/mip-jupyter:dev`).

## Build checklist

1. Run client tests: `python3 -m pytest python-client/tests -q`
2. Build single-user image: `docker build -f docker/singleuser/Dockerfile -t mip-jupyter:<tag> .`
3. Build Hub image: `docker build -f docker/hub/Dockerfile -t mip-jupyterhub:<tag> .`
4. Smoke-test the single-user container:
   - Jupyter opens at `/home/jovyan/work`
   - `Welcome.ipynb`, `examples/`, and `docs/` are visible
   - `import mip` succeeds in a notebook
   - `python-client/` and Dockerfiles are not in the file browser

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs unit tests and Docker builds on push and pull requests.

## Publishing

Image publish targets and registry credentials are configured outside this repository (platform deployment). Update `docker/hub/jupyterhub_config.py` image references when rolling out a new single-user tag.
