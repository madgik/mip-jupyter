# mip-jupyter

JupyterLab environment and the `mip` Python client for federated analysis via platform-backend.

## For production Jupyter users

When you open Jupyter in production, your working directory contains onboarding material only:

```text
Welcome.ipynb
examples/
docs/
scratch/
```

The `mip` package is pre-installed. Import it directly — you do not edit client source in this workspace:

```python
import mip

client = mip.Client.from_env()
```

Start with `Welcome.ipynb`, then see `docs/mip-client-quickstart.md` and `examples/feres_analysis.ipynb`. Save your own work under `scratch/`.

## For developers and operators

### Repository layout

| Path | Purpose |
|------|---------|
| `workspace/` | Production user-facing notebooks and docs (seeded into `/home/jovyan/work`) |
| `python-client/` | `mip` package source and tests |
| `docker/singleuser/` | Single-user Jupyter image |
| `docker/hub/` | JupyterHub image and config |
| `deploy/local/` | Local Docker Compose |
| `mip_jupyter_dev/` | Local JupyterLab runner with Codex/MCP |
| `docs/` | Architecture, layout, release process |

See [`docs/repository-layout.md`](docs/repository-layout.md) and [`docs/architecture.md`](docs/architecture.md).

### Local notebook development

Use `uv` from the repository root:

```bash
uv sync
uv run mip-notebook
```

The runner opens JupyterLab with `workspace/examples/feres_analysis.ipynb` on `127.0.0.1:8888` and token `dev`. It defaults `PLATFORM_BACKEND_URL` to `http://127.0.0.1:8080/services` unless `PLATFORM_BACKEND_URL` or `MIP_BASE_URL` is already set.

The runner also creates a temporary Codex configuration for Jupyter AI. Codex is the default chat persona and is configured to use the local North vLLM endpoint at `http://100.92.46.71:8001/v1`.

It starts a curated Jupyter MCP wrapper server by default so notebooks can be created and edited through MCP without exposing the full raw Jupyter MCP schema to North vLLM.

Codex uses that MCP server through the shell bridge `python -m mip_jupyter_dev.jupyter_mcp_cli` because North vLLM currently rejects native Responses `mcp` tool payloads with `Object of type Undefined is not JSON serializable`.

The MCP bridge uses the first free local port at or above `3001` unless `JUPYTER_MCP_PORT` or `--mcp-port` is set.

Open:

```text
http://127.0.0.1:8888/lab/tree/workspace/examples/feres_analysis.ipynb?token=dev
```

To open the getting-started notebook:

```bash
MIP_NOTEBOOK=workspace/Welcome.ipynb uv run mip-notebook
```

To override the local Codex model endpoint:

```bash
CODEX_VLLM_BASE_URL=http://127.0.0.1:8001/v1 uv run mip-notebook
```

### Install without uv

```bash
cd python-client && poetry install
```

Or:

```bash
python3 -m pip install -e ./python-client
```

### Docker images

Build from the repository root:

```bash
docker build -f docker/singleuser/Dockerfile -t mip-jupyter:latest .
docker build -f docker/hub/Dockerfile -t mip-jupyterhub:latest .
```

Local Compose:

```bash
cp deploy/local/.env.example deploy/local/.env
docker compose -f deploy/local/docker-compose.yml up --build
```

The single-user image installs `mip` as a package, seeds `/home/jovyan/work` from `workspace/`, and does not expose `python-client/` or deployment files in the Jupyter file browser.

### Quick start (API)

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

See [`expected_library.md`](expected_library.md) and [`workspace/Welcome.ipynb`](workspace/Welcome.ipynb) for the full MVP API.

### Environment variables

`Client.from_env()` reads:

- `PLATFORM_BACKEND_URL` or `MIP_BASE_URL` - platform-backend base URL, for example `http://platform-backend:8080/services`
- `PLATFORM_TOKEN` or `MIP_TOKEN` - bearer token for platform-backend
- `PLATFORM_BACKEND_TIMEOUT` - request timeout in seconds (default `30`)
- `PLATFORM_BACKEND_ALLOW_REDIRECTS` - set to `1` only when redirects should be followed

JupyterHub also injects `JUPYTERHUB_API_URL` and `JUPYTERHUB_API_TOKEN` for automatic token refresh.

Tests use mocked HTTP only and do not require live services.

### Tests

```bash
uv run python -m unittest discover -s python-client/tests -p "test_*.py"
uv run python python-client/verify_script.py
```

Without `uv`:

```bash
cd python-client && python3 -m unittest discover -s tests -p "test_*.py"
python3 python-client/verify_script.py
```

### Jupyter AI Codex prototype

The local JupyterLab runner includes Jupyter AI v3 for local agent testing. See [`docs/jupyter-ai-codex.md`](docs/jupyter-ai-codex.md) for Codex ACP setup, local North vLLM configuration, and manual verification steps.

Agent onboarding wiki: [`docs/llm/INDEX.md`](docs/llm/INDEX.md) (task-scoped docs for Jupyter AI Codex).

### Development notes

- Mock HTTP in tests; no live backend in unit tests
- Never commit real tokens
- Generated artifacts (`build/`, `*.egg-info/`, `__pycache__/`, `.venv/`) are gitignored
