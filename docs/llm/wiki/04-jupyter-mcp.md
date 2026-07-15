# Jupyter MCP — Curated Notebook and MIP Tools

**Read when:** Create, edit, run, or inspect notebooks from Jupyter AI / Codex.

**Skip if:** API-only questions (`03-mip-client-api.md`). Off-topic → `00-agent-workspace.md`.

## Shell bridge

vLLM rejects native Responses `mcp` tools. Use:

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli <command> ...
# or: jupyter-mcp <command> ...
```

`JUPYTER_MCP_URL` is set by the notebook runner.

## Tool payload safety

Keep args **small valid JSON**. Prefer a few small related calls over one giant
payload; split large edits.

**Forbidden:** `write_stdin` / heredocs / shell redirects into workspace;
giant `python -c`; `--content-file -`; paths outside the workspace; `cat` on
`.ipynb` JSON; replaying huge scripts after compaction.

**Safe:** metadata summaries → `notebook-outline` / bounded `read-cell` →
`scratch-copy-template` + `scratch-append-lines` / `scratch-replace-snippet` →
`python scratch/<name>.py` → `scratch-to-notebook`.

On **tool-call formatting errors**: new chat, `scratch-list`, resume existing
`scratch/*.py` with smaller steps.

## Common commands

```bash
# context — always prefer --topic when intent is known
jupyter-mcp read-guide --page 04-jupyter-mcp --topic payload
jupyter-mcp read-guide --page recipes/stroke-analysis --topic novel
jupyter-mcp search-docs "Client.from_env"
jupyter-mcp notebook-outline PATH
jupyter-mcp read-cell PATH INDEX --max-chars 3000

# scratch
jupyter-mcp scratch-init
jupyter-mcp scratch-list
jupyter-mcp scratch-copy-template scratch/my.py --source examples/algorithm_examples.py
jupyter-mcp scratch-append-lines scratch/my.py "# comment"
jupyter-mcp scratch-replace-snippet scratch/my.py "OLD" "NEW"
jupyter-mcp scratch-to-notebook scratch/my.py scratch/my.ipynb --title "My analysis"
jupyter-mcp scratch-log-bottleneck STEP STATUS BLOCKER "note"

# notebook
jupyter-mcp create-notebook scratch/x.ipynb
jupyter-mcp append-markdown|append-code|edit-cell|open-file ...
jupyter-mcp run-cell PATH INDEX --timeout 30   # also runs prior code cells
jupyter-mcp run-all-cells PATH --timeout 60

# MIP metadata (defaults are intentionally small)
jupyter-mcp mip-env-status
jupyter-mcp mip-catalog-summary --limit 10
jupyter-mcp mip-data-model-summary stroke --version 3.7
jupyter-mcp mip-search-variables stroke "NIHSS" --version 3.7 --limit 10
jupyter-mcp mip-algorithm-summary --limit 20
```

Exploration / bottlenecks: `read-guide --page agent-exploration`. Scripts for
notebooks should use `# %%` section markers when helpful.

## Workflow

1. `read-guide --page … --topic …` only when needed (skip INDEX/`00` by default)
2. Outline before `read-cell`
3. Substantial analysis → small scratch steps → verify → notebook
4. New notebooks under `scratch/` unless named otherwise
5. Edit by index; re-read before replying; summarize run outputs

**Next file:** the notebook you are editing, if any.
