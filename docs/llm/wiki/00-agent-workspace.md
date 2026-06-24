# Agent Workspace Guide

**Read when:** You are a Jupyter AI agent (Codex, Cursor, or MCP) assisting users in the MIP Jupyter workspace.

**Skip if:** The user task is client development — see `dev-contributor.md`.

## Workspace map

- Start with `Welcome.ipynb` for first steps and a quick MIP connection check.
- Use `examples/` for canonical examples. Read or explain them freely, but edit them only when the user explicitly asks.
- Put new or exploratory work in `scratch/`. If the user asks for a notebook without a path, create it there.
- Use `docs/` in the user workspace for user-facing help (`agent_search_docs`). Do not read `docs/user/` from the repo filesystem in production — it is copied into the user workspace at `docs/`.

## MIP scope

- Use `mip.Client.from_env()` for platform-backend access.
- Platform-backend lives behind `/services`; do not call Exaflow directly.
- Never print token values. It is fine to report whether backend URL and token configuration are present.
- Prefer metadata summaries before running analyses: catalog, data model, variable, and algorithm summaries are usually enough to plan work.

## Context order

Use the smallest source that can answer the question:

1. `agent_read_guide` (this document) on first turn.
2. `agent_search_docs(query)` for user docs in `docs/`.
3. `notebook_outline(path)` before reading notebook cells.
4. `notebook_read_cell(path, index)` for targeted cell reads.
5. MIP metadata tools for live catalog and algorithm facts.
6. Agent wiki pages under `docs/llm/wiki/` (Cursor) or `/opt/mip-agent-docs/llm/wiki/` (production MCP) for workflow and API depth.
7. Ask the user only when intent or required data is not discoverable.

## Notebook work

- Create notebooks in `scratch/` unless the user names another path.
- Read a notebook outline before editing existing notebooks.
- Edit by cell index and re-read the affected cell or outline afterwards.
- Run cells only when the user asks or when validation requires it.
- Summarize outputs and errors. Do not paste large raw outputs.

## Available curated tools

- Guide and docs: `agent_read_guide`, `agent_search_docs`.
- Notebook context: `notebook_outline`, `notebook_read_cell`.
- Notebook edits: `create_notebook`, `append_markdown_cell`, `append_code_cell`, `edit_cell_by_index`, `open_file`.
- Notebook execution: `run_cell_by_index`, `run_all_cells`.
- MIP metadata: `mip_env_status`, `mip_catalog_summary`, `mip_data_model_summary`, `mip_search_variables`, `mip_algorithm_summary`.

If native MCP tools are unavailable, call the same surface through `python -m mip_jupyter_dev.jupyter_mcp_cli`; `JUPYTER_MCP_URL` should already be set in JupyterLab.

**Next file:** `01-onboarding.md` for new-user tasks, or `04-jupyter-mcp.md` for MCP command details.
