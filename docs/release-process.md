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
   - `Welcome.ipynb`, `examples/`, `docs/`, and `scratch/` are visible
   - `docs/` contains user guides from `docs/user/` (quickstart, api-reference, troubleshooting)
   - `docs/llm/` is **not** in the file browser
   - `import mip` succeeds in a notebook
   - `python-client/` and Dockerfiles are not in the file browser
5. Verify agent docs in image (operator):
   - `ls /opt/mip-agent-docs/llm/wiki/` includes `00-agent-workspace.md`
   - `agent_read_guide` MCP tool returns content
6. Hub integration smoke (in `mip/deployment`):
   - User login → `Welcome.ipynb` → `Client.from_env()` succeeds
   - Platform token refresh works when configured

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs unit tests and Docker builds on push and pull requests.

## Publishing

Image publish targets and registry credentials are configured in **`mip/deployment`**. Update `docker/hub/jupyterhub_config.py` image references when rolling out a new single-user tag.
