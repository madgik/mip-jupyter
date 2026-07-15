# Agent Exploration — Bottleneck Tracking

**Read when:** Running a multi-step exploration, catalog audit, or novel stroke analysis with Cohort Scout.

**Skip if:** Single small notebook edit (`04-jupyter-mcp.md` is enough).

## Turn 1 setup (mandatory)

1. `read-guide --page agent-exploration` (this page)
2. `scratch-list` — resume existing artifacts before creating new scripts
3. `scratch-init` (or `scratch-copy-file` for individual templates)
4. Fill objective and primary hypothesis in `_session.md`

## Phased workflow

| Phase | Action |
|-------|--------|
| **A — Discovery** | `mip-env-status`, `mip-data-model-summary stroke --version 3.7`, `python scratch/stroke_preflight.py` |
| **B — Catalog audit** | `mip-algorithm-summary`, `read-guide --page 07-pipeline-algorithms`; signatures from `examples/algorithm_examples.py` |
| **C — Novel analysis** | `scratch-copy-template scratch/<name>.py --source examples/algorithm_examples.py`, trim to one hypothesis, small edits, run script |
| **D — Notebook** | `scratch-to-notebook`, `notebook-outline`, `open-file` |

Do **not** stop after Phase B metadata alone. Complete Phase C unless preflight fails.

## Bottleneck logging

After every tool call or script run:

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli scratch-log-bottleneck STEP STATUS BLOCKER "note"
```

| Field | Values |
|-------|--------|
| **status** | `ok`, `failed`, `skipped`, `investigate` |
| **blocker** | `wrong_api`, `not_wrapped`, `platform_error`, `missing_variable`, `empty_cohort`, `tool_limit`, `agent_tooling`, or `-` |

Log **full** error messages in `note` — never truncate platform errors.

## Blocker taxonomy

- **wrong_api** — `TypeError` from wrong kwargs; fix using `examples/algorithm_examples.py` signatures
- **not_wrapped** — method not in `pipeline.available_algorithms()` (30 methods)
- **platform_error** — experiment `status='error'`
- **missing_variable** / **empty_cohort** — SSR data or filter issue
- **tool_limit** — payload too large; split scratch edits
- **agent_tooling** — MCP or shell guard rejection

## Resume after tool-call error

1. New chat
2. `scratch-list`
3. Continue your `scratch/<name>.py`
4. `scratch-append-lines` / `scratch-replace-snippet` only (max 20 lines per call)

## Reference signatures

Use only:

- `workspace/examples/algorithm_examples.py`
- `workspace/examples/feres_analysis.ipynb` (patterns)

Do not invent methods (`median_survival_time`, etc.) or sklearn-style `x=`/`y=` kwargs.

## Deliverables (session end)

1. Runnable `scratch/<name>.py` and optional `.ipynb`
2. Updated `scratch/_bottlenecks.md`
3. Chat summary: primary OR (95% CI) if logistic run, top 5 bottlenecks, next human fix

## Starter prompt (user paste)

```text
Exploration on Stroke 3.7 / SSR. Turn 1: scratch-init + scratch-list.
Phases A–D. scratch-log-bottleneck after each step.
Novel work: copy from examples/algorithm_examples.py, not a shipped starter template.
End with OR (95% CI), top 5 bottlenecks, next action.
```

**Next file:** [`recipes/stroke-analysis.md`](recipes/stroke-analysis.md) for novel inference rules.
