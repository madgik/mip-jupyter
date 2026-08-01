# Agent Exploration

**Read when:** Multi-step exploration, catalog audit, or novel stroke analysis with Cohort Scout.

**Skip if:** Single small notebook edit (`04-jupyter-mcp.md` is enough).

Use `CODEX_REASONING_EFFORT=medium` for this workflow if the default is `low`.

Skip this page for a single small notebook tweak — use direct notebook tools
(`create-notebook` / `append-*` / `edit-cell`) per `04-jupyter-mcp.md`.

## Direct notebook vs scratch first

| Choose | When |
|--------|------|
| **Direct notebook** | Markdown, one small code cell, outline/read, rename/create empty notebook, fix one cell |
| **Scratch first** | Multi-step MIP client work, federated algorithms, script validation before user-facing cells |
| **Always after scratch** | `python scratch/<name>.py` (exit 0) → `scratch-to-notebook` → `open-file` / `notebook-outline` |

## Turn 1 setup

1. `jupyter-mcp read-guide --page agent-exploration` (this page)
2. `jupyter-mcp scratch-list` — resume existing artifacts before creating new scripts

## Phased workflow

| Phase | Action |
|-------|--------|
| **A — Discovery** | `jupyter-mcp mip-env-status`, `mip-data-model-summary stroke --version 3.7`, `python scratch/stroke_preflight.py` |
| **B — Catalog audit** | `jupyter-mcp mip-algorithm-summary`, `jupyter-mcp read-guide --page 07-pipeline-algorithms`; signatures from `examples/algorithm_examples.py` |
| **C — Novel analysis** | `jupyter-mcp scratch-copy-template scratch/<name>.py --source examples/algorithm_examples.py`, trim to one hypothesis, small edits, **`python scratch/<name>.py`** until exit 0 |
| **D — Notebook** | `jupyter-mcp scratch-to-notebook`, `notebook-outline`, `open-file` |

Do **not** stop after Phase B metadata alone. Complete Phase C unless preflight fails.
Do **not** stop at a verified `.py` alone — finish Phase D unless the user asked for a script only.

## Resume after tool-call error

1. New chat → `scratch-list` → continue newest complete `scratch/<name>.py`
2. `scratch-append-lines` / `scratch-replace-snippet` only (max 20 lines per call)

## Reference signatures

Use `workspace/examples/algorithm_examples.py` and `feres_analysis.ipynb` patterns.
Do not invent methods or sklearn-style `x=`/`y=` kwargs.

## Deliverables (session end)

1. Runnable `scratch/<name>.py` and optional `.ipynb`
2. Chat summary: primary OR (95% CI) if logistic run, next human fix

## Starter prompt (user paste)

```text
Exploration on Stroke 3.7 / SSR. Turn 1: scratch-list.
Phases A–D.
Novel work: copy from examples/algorithm_examples.py.
End with OR (95% CI) and next action.
```

**Next file:** [`recipes/stroke-analysis.md`](recipes/stroke-analysis.md) for novel inference rules.
