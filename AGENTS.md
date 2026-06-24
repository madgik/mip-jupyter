# MIP Jupyter — Agent Bootstrap

You are a Jupyter AI agent working in **mip-jupyter**: JupyterLab plus the `mip` Python client for federated analysis via platform-backend.

## Scope

- Notebooks use `mip` → platform-backend (`/services`) only. Never call Exaflow directly.
- Stay in this repository. Do not read sibling repos or umbrella workspace docs.

## Startup (required)

1. Read [docs/llm/INDEX.md](docs/llm/INDEX.md)
2. Open the **one** wiki page for the user's task (routing table below)
3. Open source files or notebooks only when that page says so

## Routing

| Task | Wiki page |
|------|-----------|
| Agent workspace rules, MCP workflow | [docs/llm/wiki/00-agent-workspace.md](docs/llm/wiki/00-agent-workspace.md) |
| New MIP user, first steps | [docs/llm/wiki/01-onboarding.md](docs/llm/wiki/01-onboarding.md) |
| Build or run an analysis pipeline | [docs/llm/wiki/02-analysis-workflow.md](docs/llm/wiki/02-analysis-workflow.md) |
| MIP Python API lookup | [docs/llm/wiki/03-mip-client-api.md](docs/llm/wiki/03-mip-client-api.md) |
| Create or edit notebooks via AI | [docs/llm/wiki/04-jupyter-mcp.md](docs/llm/wiki/04-jupyter-mcp.md) |
| Env vars, `Client.from_env()` | [docs/llm/wiki/05-env-and-backend.md](docs/llm/wiki/05-env-and-backend.md) |
| Stroke pathology notebook | [docs/llm/wiki/recipes/stroke-analysis.md](docs/llm/wiki/recipes/stroke-analysis.md) |
| Client dev, tests, commits | [docs/llm/wiki/dev-contributor.md](docs/llm/wiki/dev-contributor.md) |

## Key files

| File | Purpose |
|------|---------|
| `workspace/Welcome.ipynb` | Getting-started runnable notebook |
| `workspace/examples/feres_analysis.ipynb` | Stroke territory analysis example |
| `docs/user/` | User-facing docs (shipped to workspace `docs/`; quote to users, not agent startup) |
| `expected_library.md` | Full API contract (read only when cheat sheet is insufficient) |

## Tools

Notebook create/edit: `python -m mip_jupyter_dev.jupyter_mcp_cli` (`JUPYTER_MCP_URL` is set). See `04-jupyter-mcp.md` for commands.

## Guardrails

- No full-repo `find`, `grep`, or directory listing on startup
- Do not read `expected_library.md` unless `03-mip-client-api.md` is insufficient
- Do not read `.venv/`, `.ipynb_checkpoints/`, `.playwright-cli/`, or `uv.lock`
- Never log or commit tokens (`MIP_TOKEN`, `PLATFORM_TOKEN`)

## Repository layout (brief)

- `workspace/` — production user-facing notebooks (docs copied from `docs/user/` at image build)
- `docs/user/` — canonical user documentation source
- `python-client/mip/` — client library source
- `docker/` — single-user and Hub image definitions
- `mip_jupyter_dev/` — local JupyterLab runner and MCP bridge
- `docs/llm/` — task-scoped agent wiki

For build, test, and PR rules see [docs/llm/wiki/dev-contributor.md](docs/llm/wiki/dev-contributor.md).
