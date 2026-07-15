# Jupyter MCP — Curated Notebook and MIP Tools

**Read when:** You must create, edit, run, or inspect notebooks from Jupyter AI Codex.

**Skip if:** The user only asks about MIP analysis API (see `03-mip-client-api.md`).

Off-topic requests are out of scope — see `00-agent-workspace.md`.

## Why the shell bridge

The vLLM Responses shim rejects native `mcp` tool payloads. Codex calls curated tools through:

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli <command> ...
```

`JUPYTER_MCP_URL` is set by the notebook runner.

## Tool payload safety (vLLM)

Keep every tool-call argument **small and valid JSON**. One command per turn when possible.

### Forbidden

- `write_stdin` for multi-line code
- Heredocs: `cat > file << 'EOF'`
- Shell redirects into `scratch/` or `workspace/`
- Giant `python -c "..."` blocks (more than a few lines)
- Piping large bodies via `--content-file -`
- `--content-file` paths outside the Jupyter workspace
- `cat notebook.ipynb | python -c` to parse JSON
- Replaying 500+ line scripts after compaction

### Safe patterns

1. Bounded discovery: `mip-env-status`, `mip-data-model-summary`, `mip-search-variables`
2. `notebook-outline` then `read-cell` with `--max-chars`
3. Novel/multi-step analysis:
   - `scratch-copy-template scratch/<name>.py`
   - `scratch-append-lines` / `scratch-replace-snippet` for small edits
   - `python scratch/<name>.py` to verify
   - `scratch-to-notebook scratch/<name>.py scratch/<name>.ipynb --title "<name>"`
4. Transfer verified flow into notebook cells incrementally

`--content-file path` is for modest cell bodies from a **workspace-relative** path only. For substantial code, use scratch tools — not shell writes.

### Recovery

If Cohort Scout reports a **tool-call formatting error**, start a **new chat** and retry with a smaller step. Resume from existing `scratch/*.py` artifacts instead of regenerating large scripts. Your notebook and MIP connection are unaffected.

## Scratch edit commands

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli scratch-init
python -m mip_jupyter_dev.jupyter_mcp_cli scratch-copy-file scratch/_session.md scratch/_session.template.md
python -m mip_jupyter_dev.jupyter_mcp_cli scratch-read scratch/_session.md --max-chars 4000
python -m mip_jupyter_dev.jupyter_mcp_cli scratch-copy-template scratch/my_analysis.py --source examples/algorithm_examples.py
python -m mip_jupyter_dev.jupyter_mcp_cli scratch-append-lines scratch/my_analysis.py "# comment"
python -m mip_jupyter_dev.jupyter_mcp_cli scratch-replace-snippet scratch/my_analysis.py "OLD" "NEW"
python -m mip_jupyter_dev.jupyter_mcp_cli scratch-to-notebook scratch/my_analysis.py scratch/my_analysis.ipynb --title "My analysis"
python -m mip_jupyter_dev.jupyter_mcp_cli scratch-list
python -m mip_jupyter_dev.jupyter_mcp_cli scratch-log-bottleneck t_test failed platform_error "full error message"
```

Exploration workflow and bottleneck taxonomy: `read-guide --page agent-exploration`.

Scripts transferred to notebooks should include `# %%` section markers when splitting cells (see `examples/algorithm_examples.py`).

## Context commands

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli read-guide
python -m mip_jupyter_dev.jupyter_mcp_cli read-guide --page index
python -m mip_jupyter_dev.jupyter_mcp_cli read-guide --page recipes/stroke-analysis --topic "pipeline"
python -m mip_jupyter_dev.jupyter_mcp_cli search-docs "Client.from_env"
python -m mip_jupyter_dev.jupyter_mcp_cli notebook-outline workspace/examples/feres_analysis.ipynb
python -m mip_jupyter_dev.jupyter_mcp_cli read-cell workspace/examples/feres_analysis.ipynb 3 --max-chars 4000
```

## Notebook edit commands

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli create-notebook scratch/mcp_probe.ipynb
python -m mip_jupyter_dev.jupyter_mcp_cli append-markdown scratch/mcp_probe.ipynb "# Probe"
python -m mip_jupyter_dev.jupyter_mcp_cli append-code scratch/mcp_probe.ipynb "import mip"
python -m mip_jupyter_dev.jupyter_mcp_cli edit-cell scratch/mcp_probe.ipynb 0 "# Updated" --cell-type markdown
python -m mip_jupyter_dev.jupyter_mcp_cli open-file scratch/mcp_probe.ipynb
```

## Execution commands

`run-cell` executes the selected cell **and all prior code cells** in the same kernel (Jupyter-like). Use `run-all-cells` for full-notebook execution.

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli run-cell scratch/mcp_probe.ipynb 1 --timeout 30
python -m mip_jupyter_dev.jupyter_mcp_cli run-all-cells scratch/mcp_probe.ipynb --timeout 60
```

Run cells only when the user asks or validation requires it. Summarize outputs; do not paste large raw outputs.

## MIP metadata commands

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli mip-env-status
python -m mip_jupyter_dev.jupyter_mcp_cli mip-catalog-summary --limit 20
python -m mip_jupyter_dev.jupyter_mcp_cli mip-data-model-summary stroke --version 3.7
python -m mip_jupyter_dev.jupyter_mcp_cli mip-search-variables stroke "NIHSS" --version 3.7
python -m mip_jupyter_dev.jupyter_mcp_cli mip-algorithm-summary
```

CLI data-model lookup uses `stroke --version 3.7`, not a positional `3.7` argument.

## Workflow

1. Read `read-guide --page PAGE` only when workflow detail is needed.
2. `notebook-outline` before targeted `read-cell` calls.
3. For substantial analysis, build `scratch/*.py` in small steps, verify, then transfer to notebook cells.
4. Create new notebooks in `scratch/` unless the user names another path.
5. Edit by index; re-read the affected cell or outline before replying.

**Next file:** The target notebook you are editing, if any.
