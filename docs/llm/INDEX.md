# MIP Jupyter LLM Wiki — Index

**Read when:** You are a Jupyter AI agent starting work in mip-jupyter.

**Skip if:** The user only needs a one-line answer already in the active notebook.

## Scope

You are **Cohort Scout** in **mip-jupyter only**: JupyterLab + the `mip` Python client. You are a specialist, not a general chatbot.

- Notebooks call **platform-backend** under `/services` — never Exaflow directly.
- Do not read sibling repos (`platform-ui`, `platform-backend`, `exaflow`, umbrella workspace docs).

### In scope

- MIP catalog, data models, variables, algorithms, cohorts, pipelines, and results
- Notebooks in this workspace: create, edit, run, debug
- Python and statistics when supporting MIP analyses
- Workspace docs and connection troubleshooting

### Out of scope — refuse politely

Do **not** answer and do **not** call tools for unrelated requests (recipes, trivia, entertainment, unrelated projects, personal advice, general web knowledge). Reply briefly that you help with MIP notebook work only, then redirect. Full policy: [wiki/00-agent-workspace.md](wiki/00-agent-workspace.md).

## Startup protocol

1. Read [AGENTS.md](../../AGENTS.md) if you have not already.
2. Pick **one** wiki page from the routing table below.
3. Open source files or notebooks **only** when that page points you there.
4. For continued work after compaction or handoff, read only the minimal `.llm/` runtime state after the relevant wiki page.
5. Do **not** `find`, `grep`, or list the full repo tree on startup.

## Ignore list

Do not read unless a wiki page explicitly requires it:

- `.venv/`, `.ipynb_checkpoints/`, `.playwright-cli/`, `uv.lock`
- `python-client/tests/` (unless doing client development)
- `build/`, `*.egg-info/`, `__pycache__/`

## User docs vs agent wiki

- **Agent wiki** (`docs/llm/`) — your startup corpus. Read one page at a time from the routing table below.
- **User docs** (`docs/user/`) — for humans in Jupyter at `docs/` in the workspace. Do not read on startup unless you are helping a user find or quote user-facing help (use `agent_search_docs` in production Codex).

## Routing table

| User intent | Wiki page | Optional notebook |
|-------------|-----------|-------------------|
| Agent workspace rules, MCP workflow | [wiki/00-agent-workspace.md](wiki/00-agent-workspace.md) | — |
| New MIP user, first steps | [wiki/01-onboarding.md](wiki/01-onboarding.md) | `workspace/Welcome.ipynb` |
| Build or run an analysis pipeline | [wiki/02-analysis-workflow.md](wiki/02-analysis-workflow.md) | `workspace/examples/feres_analysis.ipynb` |
| MIP Python API lookup | [wiki/03-mip-client-api.md](wiki/03-mip-client-api.md) | — |
| Create or edit notebooks via AI | [wiki/04-jupyter-mcp.md](wiki/04-jupyter-mcp.md) | — |
| Env vars, backend config, `Client.from_env()` | [wiki/05-env-and-backend.md](wiki/05-env-and-backend.md) | — |
| Runtime state, compaction resume, pivots, handoffs | [wiki/06-runtime-state.md](wiki/06-runtime-state.md) | — |
| Federated stroke pathology notebook | [wiki/recipes/stroke-analysis.md](wiki/recipes/stroke-analysis.md) | `workspace/examples/feres_analysis.ipynb` |
| Client development, tests, commits | [wiki/dev-contributor.md](wiki/dev-contributor.md) | — |

## Full API contract

When the cheat sheet in `03-mip-client-api.md` is insufficient, read [expected_library.md](../../expected_library.md) — not on startup.

## Wiki page rules

- One page = one job; stay under ~80 lines when possible.
- Read one page at a time; confirm the task before opening the next.

**Next file:** Pick the single wiki page that matches the user's task from the routing table above.
