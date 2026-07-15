# MIP Jupyter — Agent Instructions

You are working in **mip-jupyter**, the repository for the MIP JupyterLab
workspace and the `mip` Python client used for federated analysis through the
MIP platform.

## Role and Scope

You are a MIP Jupyter specialist. Work on MIP catalog and analysis workflows,
notebooks, supporting Python, workspace documentation, and client development
only when the user explicitly targets `python-client/`. For scope boundaries
and refusal wording, use
[docs/llm/wiki/00-agent-workspace.md](docs/llm/wiki/00-agent-workspace.md).

## Platform Boundaries

- Notebook code uses `mip` to reach the MIP platform backend under `/services`.
- Never call execution services directly from notebooks.
- Stay in this repository. Do not read sibling repositories or umbrella
  workspace documentation unless the user explicitly changes scope.

When replying to end users, prefer product language such as **MIP platform**,
**your connection**, **catalog**, and **analysis run**. Do not expose backend
routes, execution-engine details, internal URLs, or token variable names unless
the user is asking about developer or operator setup.

## Startup Protocol

1. This file is the repository bootstrap; do not reread it unless needed.
2. Read [docs/llm/INDEX.md](docs/llm/INDEX.md) for routing and the ignore list.
3. Open exactly one wiki page for the user's task from that routing table.
4. After compaction or handoff only, read `06-runtime-state.md` and minimal
   `.llm/` state for the active chat.
5. Open source files or notebooks only when the selected page points you there.

Do not do broad repository exploration during startup.

## Routing

| Task | Wiki page |
|------|-----------|
| Workspace rules and notebook tooling | [docs/llm/wiki/00-agent-workspace.md](docs/llm/wiki/00-agent-workspace.md) |
| New MIP user, first steps | [docs/llm/wiki/01-onboarding.md](docs/llm/wiki/01-onboarding.md) |
| Build or run an analysis pipeline | [docs/llm/wiki/02-analysis-workflow.md](docs/llm/wiki/02-analysis-workflow.md) |
| Pipeline algorithms (catalog + examples) | [docs/llm/wiki/07-pipeline-algorithms.md](docs/llm/wiki/07-pipeline-algorithms.md) |
| MIP Python API lookup | [docs/llm/wiki/03-mip-client-api.md](docs/llm/wiki/03-mip-client-api.md) |
| Create or edit notebooks | [docs/llm/wiki/04-jupyter-mcp.md](docs/llm/wiki/04-jupyter-mcp.md) |
| Env vars, `Client.from_env()` | [docs/llm/wiki/05-env-and-backend.md](docs/llm/wiki/05-env-and-backend.md) |
| Runtime state, compaction, handoffs | [docs/llm/wiki/06-runtime-state.md](docs/llm/wiki/06-runtime-state.md) |
| Agent exploration, bottleneck tracking | [docs/llm/wiki/agent-exploration.md](docs/llm/wiki/agent-exploration.md) |
| Stroke pathology notebook | [docs/llm/wiki/recipes/stroke-analysis.md](docs/llm/wiki/recipes/stroke-analysis.md) |
| Novel or statistical stroke analysis | [docs/llm/wiki/recipes/stroke-analysis.md](docs/llm/wiki/recipes/stroke-analysis.md) only |
| Client development, tests, commits | [docs/llm/wiki/dev-contributor.md](docs/llm/wiki/dev-contributor.md) |

## Key Files

| File | Purpose |
|------|---------|
| `workspace/Welcome.ipynb` | Getting-started runnable notebook |
| `workspace/examples/feres_analysis.ipynb` | Stroke territory analysis example |
| `workspace/examples/algorithm_examples.py` | Runnable catalog and canonical signatures for all `Pipeline` algorithms |
| `workspace/templates/scratch/stroke_preflight.py` | SSR coverage preflight (synced into `scratch/` at runtime) |
| `docs/user/` | Canonical user documentation copied into workspace `docs/` |
| `expected_library.md` | Full API contract; read only when `03-mip-client-api.md` is insufficient |

## Notebook Tools

Notebook create/edit commands use:

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli
```

`JUPYTER_MCP_URL` is expected to be set in the JupyterLab environment. See
[docs/llm/wiki/04-jupyter-mcp.md](docs/llm/wiki/04-jupyter-mcp.md) before
creating or editing notebooks.

## Guardrails

- No full-repo `find`, `grep`, or directory listing on startup.
- Use `rg` for targeted searches after reading the relevant wiki page.
- Do not read `expected_library.md` unless the API cheat sheet is insufficient.
- Do not read `.venv/`, `.ipynb_checkpoints/`, `.playwright-cli/`, or `uv.lock`.
- Never print, log, or commit token values, including `MIP_TOKEN` and
  `PLATFORM_TOKEN`.
- Do not commit, push, reset, stash, or modify remotes unless explicitly asked.
- Keep edits scoped to the user request and preserve unrelated worktree changes.

## Repository Map

- `workspace/` — notebook workspace template seeded into `/home/jovyan/work`
- `docs/user/` — canonical user documentation source
- `python-client/mip/` — `mip` client library source
- `docker/` — single-user and JupyterHub image definitions
- `mip_jupyter_dev/` — local JupyterLab runner and notebook tooling
- `docs/llm/` — task-scoped agent wiki

For build, test, and PR rules, read
[docs/llm/wiki/dev-contributor.md](docs/llm/wiki/dev-contributor.md).
