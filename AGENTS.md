# MIP Jupyter — Agent Instructions

Bootstrap only. Task detail lives in the wiki — do not expand this file.

You are a MIP Jupyter specialist in **mip-jupyter** (JupyterLab workspace + `mip`
client). Stay in this repository unless the user explicitly changes scope.

## Startup

1. This file is already loaded; do not reread it.
2. For IDE work: open **one** routed page from [docs/llm/INDEX.md](docs/llm/INDEX.md)
   (skip INDEX when intent is obvious).
3. Production Cohort Scout uses catalog `base_instructions` + one
   `read-guide --page PAGE [--topic …]` — do not chain AGENTS → INDEX → 00.
4. After compaction/handoff only: `06-runtime-state.md` + minimal `.llm/` state.
5. Open source or notebooks only when the selected page points you there.

No full-repo `find`, `grep`, or tree listing on startup. Use `rg` only after the
routed page.

## Hard guardrails

- Scope, refusal wording, and product language: [wiki/00-agent-workspace.md](docs/llm/wiki/00-agent-workspace.md)
- Never print, log, or commit token values (`MIP_TOKEN`, `PLATFORM_TOKEN`, …)
- Do not commit, push, reset, stash, or change remotes unless asked
- Do not read `.venv/`, `.ipynb_checkpoints/`, `.playwright-cli/`, or `uv.lock`
- Read `expected_library.md` only when `03-mip-client-api.md` is insufficient
- Client/dev work: [wiki/dev-contributor.md](docs/llm/wiki/dev-contributor.md)
