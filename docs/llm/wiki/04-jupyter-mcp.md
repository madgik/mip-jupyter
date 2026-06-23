# Jupyter MCP — Notebook Edits via Shell Bridge

**Read when:** You must create, edit, or read notebooks from Jupyter AI Codex.

**Skip if:** The user only asks about MIP analysis API (see `03-mip-client-api.md`).

## Why the shell bridge

North vLLM rejects native Responses `mcp` tool payloads. Codex calls the Jupyter MCP server through:

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli <command> ...
```

`JUPYTER_MCP_URL` is set by the notebook runner. Do not ask the user to paste notebook cells manually.

## Commands

```bash
# Create notebook
python -m mip_jupyter_dev.jupyter_mcp_cli create-notebook path.ipynb

# Add cells
python -m mip_jupyter_dev.jupyter_mcp_cli add-markdown path.ipynb "Title text"
python -m mip_jupyter_dev.jupyter_mcp_cli add-code path.ipynb "import mip"

# Edit cell by index (0-based)
python -m mip_jupyter_dev.jupyter_mcp_cli edit-cell path.ipynb 0 "new content" --cell-type markdown

# Read cells (verify before replying)
python -m mip_jupyter_dev.jupyter_mcp_cli read-notebook path.ipynb

# Open in JupyterLab
python -m mip_jupyter_dev.jupyter_mcp_cli open-file path.ipynb

# Run all cells in active notebook
python -m mip_jupyter_dev.jupyter_mcp_cli run-all-cells
```

Multi-line cell content: use `--content-file path` or pipe via `--content-file -`.

## Workflow

1. `create-notebook` (if new)
2. `add-markdown` / `add-code` for each cell
3. `read-notebook` to confirm cells before replying DONE

## When to read `.ipynb` directly

Use `read-notebook` or filesystem read when inspecting existing notebooks. Use MCP for creates and edits so changes appear in JupyterLab.

## Verify MCP server

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli read-notebook workspace/examples/feres_analysis.ipynb
```

**Next file:** The target notebook you are editing.
