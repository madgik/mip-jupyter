# mip-jupyter

JupyterLab environment and the `mip` Python client for federated analysis via platform-backend.

## For Jupyter users

When you open Jupyter in production, your working directory contains:

```text
Welcome.ipynb
examples/
docs/
scratch/
```

The `mip` package is pre-installed:

```python
import mip

client = mip.Client.from_env()
```

**Start here:** `Welcome.ipynb` → `docs/quickstart.md` → `examples/feres_analysis.ipynb`. Save your own work under `scratch/`.

User documentation source: [`docs/user/`](docs/user/) (copied into `docs/` in the Jupyter workspace at image build).

## For developers

### Local notebook development

```bash
uv sync
uv run mip-notebook
```

Opens JupyterLab at `127.0.0.1:8888` (token `dev`) with `workspace/examples/feres_analysis.ipynb` by default. The runner syncs `docs/user/` into `workspace/docs/` and sets `PLATFORM_BACKEND_URL` to `http://127.0.0.1:8080/services` unless already configured.

```bash
MIP_NOTEBOOK=workspace/Welcome.ipynb uv run mip-notebook
```

See [`docs/llm/wiki/dev-contributor.md`](docs/llm/wiki/dev-contributor.md) for tests, client development, and commit guidelines.

Agent onboarding: [`AGENTS.md`](AGENTS.md) → [`docs/llm/INDEX.md`](docs/llm/INDEX.md).

### Repository layout

| Path | Purpose |
|------|---------|
| `workspace/` | Notebooks seeded into `/home/jovyan/work` |
| `docs/user/` | Canonical user documentation |
| `docs/llm/` | Agent wiki (`AGENTS.md` bootstrap) |
| `python-client/` | `mip` package source and tests |
| `docker/` | Single-user and Hub image definitions |
| `mip_jupyter_dev/` | Local JupyterLab runner with Codex/MCP |

See [`docs/repository-layout.md`](docs/repository-layout.md) and [`docs/architecture.md`](docs/architecture.md).

### Install and test

```bash
cd python-client && poetry install
python3 -m pip install -e ./python-client
uv run python -m pytest python-client/tests -q
uv run python python-client/verify_script.py
```

### Docker images

Build from the repository root:

```bash
docker build -f docker/singleuser/Dockerfile -t mip-jupyter:latest .
docker build -f docker/hub/Dockerfile -t mip-jupyterhub:latest .
```

See [`docs/release-process.md`](docs/release-process.md) for the release checklist.

### Environment variables

`Client.from_env()` reads:

- `PLATFORM_BACKEND_URL` or `MIP_BASE_URL` — platform-backend base URL under `/services`
- `PLATFORM_TOKEN` or `MIP_TOKEN` — bearer token
- `PLATFORM_BACKEND_TIMEOUT` — request timeout in seconds (default `30`)
- `PLATFORM_BACKEND_ALLOW_REDIRECTS` — set to `1` to follow redirects

JupyterHub may inject `JUPYTERHUB_API_URL` and `JUPYTERHUB_API_TOKEN` for token refresh.

### Jupyter AI Codex prototype

See [`docs/jupyter-ai-codex.md`](docs/jupyter-ai-codex.md) for local Codex/MCP setup.

## For operators

Deployment, Hub configuration, Keycloak, and image rollout are owned by **`mip/deployment`**, not this repository.

See [`docs/operators.md`](docs/operators.md) for what mip-jupyter provides and how it integrates with platform deployment.
