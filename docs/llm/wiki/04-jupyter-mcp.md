# Jupyter MCP — Curated Notebook and MIP Tools

**Read when:** You must create, edit, run, or inspect notebooks from Jupyter AI Codex.

**Skip if:** The user only asks about MIP analysis API (see `03-mip-client-api.md`).

Off-topic requests (recipes, trivia, unrelated projects) are out of scope — see `00-agent-workspace.md`. Do not call MCP tools for them.

## Why the shell bridge

qwen36-nvfp4 rejects native Responses `mcp` tool payloads on qwen vLLM. Codex calls the same curated Jupyter MCP tools through:

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli <command> ...
```

`JUPYTER_MCP_URL` is set by the notebook runner. Do not ask the user to paste notebook cells manually.

## Context commands

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli read-guide
python -m mip_jupyter_dev.jupyter_mcp_cli search-docs "Client.from_env"
python -m mip_jupyter_dev.jupyter_mcp_cli notebook-outline workspace/examples/feres_analysis.ipynb
python -m mip_jupyter_dev.jupyter_mcp_cli read-cell workspace/examples/feres_analysis.ipynb 3 --max-chars 4000
```

`notebook-outline` returns cell indexes, headings, source previews, and output/error counts. It does not return full outputs.

## Notebook edit commands

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli create-notebook scratch/mcp_probe.ipynb
python -m mip_jupyter_dev.jupyter_mcp_cli append-markdown scratch/mcp_probe.ipynb "# Probe"
python -m mip_jupyter_dev.jupyter_mcp_cli append-code scratch/mcp_probe.ipynb "import mip"
python -m mip_jupyter_dev.jupyter_mcp_cli edit-cell scratch/mcp_probe.ipynb 0 "# Updated" --cell-type markdown
python -m mip_jupyter_dev.jupyter_mcp_cli open-file scratch/mcp_probe.ipynb
```

Multi-line cell content: use `--content-file path` or pipe via `--content-file -`.

## Execution commands

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli run-cell scratch/mcp_probe.ipynb 1 --timeout 30
python -m mip_jupyter_dev.jupyter_mcp_cli run-all-cells scratch/mcp_probe.ipynb --timeout 60
```

Run cells only when the user asks or validation requires it. Summarize outputs and errors; do not paste large raw outputs.

## MIP metadata commands

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli mip-env-status
python -m mip_jupyter_dev.jupyter_mcp_cli mip-catalog-summary --limit 20
python -m mip_jupyter_dev.jupyter_mcp_cli mip-data-model-summary dementia --version 0.1
python -m mip_jupyter_dev.jupyter_mcp_cli mip-search-variables stroke "NIHSS" --version 3.7
python -m mip_jupyter_dev.jupyter_mcp_cli mip-algorithm-summary
```

These commands use `mip.Client.from_env()` and MIP platform metadata only. They never print token values.

## Workflow

1. `read-guide`, then `search-docs` for user-facing docs.
2. `notebook-outline` before targeted `read-cell` calls.
3. Create new notebooks in `scratch/` unless the user names another path.
4. Edit by index, then re-read the affected cell or outline before replying.

Legacy aliases still exist for `add-markdown`, `add-code`, and `read-notebook`, but prefer the commands above.

**Next file:** The target notebook you are editing, if any.
