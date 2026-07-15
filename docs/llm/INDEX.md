# MIP Jupyter LLM Wiki — Index

**Read when:** You are a Jupyter AI agent starting work in mip-jupyter.

**Skip if:** The user only needs a one-line answer already in the active notebook.

## Scope

Role, platform boundaries, and refusal wording live in
[wiki/00-agent-workspace.md](wiki/00-agent-workspace.md). This index only routes
startup context and defines what is safe to defer.

## Startup protocol

1. The repository supplies `AGENTS.md` as the bootstrap; do not reread it here.
2. Pick **one** wiki page from the routing table below.
3. Open source files or notebooks **only** when that page points you there.
4. For continued work after compaction or handoff, read `06-runtime-state.md`
   and only the minimal `.llm/` runtime state for the active chat.
5. Do **not** `find`, `grep`, or list the full repo tree on startup.

## Ignore list

Do not read unless a wiki page explicitly requires it:

- `.venv/`, `.ipynb_checkpoints/`, `.playwright-cli/`, `uv.lock`
- `python-client/tests/` (unless doing client development)
- `build/`, `*.egg-info/`, `__pycache__/`

## User docs vs agent wiki

- **Agent wiki** (`docs/llm/`) — your startup corpus. Read one page at a time from the routing table below.
- **User docs** (`docs/user/`) — for humans in Jupyter at `docs/` in the workspace. Do not read on startup unless you are helping a user find or quote user-facing help (use `agent_search_docs` in production Codex).
- **Production Codex wiki access** — use `read-guide --page PAGE` through the Jupyter MCP shell bridge; never scan the bundled wiki directly.

## Routing table

| User intent | Wiki page | Optional notebook |
|-------------|-----------|-------------------|
| Agent workspace rules, MCP workflow | [wiki/00-agent-workspace.md](wiki/00-agent-workspace.md) | — |
| New MIP user, first steps | [wiki/01-onboarding.md](wiki/01-onboarding.md) | `workspace/Welcome.ipynb` |
| Build or run an analysis pipeline | [wiki/02-analysis-workflow.md](wiki/02-analysis-workflow.md) | `workspace/examples/feres_analysis.ipynb` |
| Which algorithms exist and how to run them | [wiki/07-pipeline-algorithms.md](wiki/07-pipeline-algorithms.md) | `workspace/examples/algorithm_examples.py` |
| MIP Python API lookup | [wiki/03-mip-client-api.md](wiki/03-mip-client-api.md) | — |
| Create or edit notebooks via AI | [wiki/04-jupyter-mcp.md](wiki/04-jupyter-mcp.md) | — |
| Env vars, backend config, `Client.from_env()` | [wiki/05-env-and-backend.md](wiki/05-env-and-backend.md) | — |
| Runtime state, compaction resume, pivots, handoffs | [wiki/06-runtime-state.md](wiki/06-runtime-state.md) | — |
| Agent exploration, catalog audit, bottleneck tracking | [wiki/agent-exploration.md](wiki/agent-exploration.md) | `workspace/scratch/README.md` |
| Federated stroke pathology notebook | [wiki/recipes/stroke-analysis.md](wiki/recipes/stroke-analysis.md) | `workspace/examples/feres_analysis.ipynb` |
| Novel or statistical stroke analysis | [wiki/recipes/stroke-analysis.md](wiki/recipes/stroke-analysis.md) only — do not chain `02`/`03`/`04` | `scratch-copy-template` from `examples/algorithm_examples.py`, then `scratch-to-notebook` |
| Client development, tests, commits | [wiki/dev-contributor.md](wiki/dev-contributor.md) | — |

## Full API contract

When the cheat sheet in `03-mip-client-api.md` is insufficient, read [expected_library.md](../../expected_library.md) — not on startup.

## Wiki page rules

- One page = one job; stay under ~80 lines when possible.
- Read one page at a time; confirm the task before opening the next.

**Next file:** Pick the single wiki page that matches the user's task from the routing table above.
