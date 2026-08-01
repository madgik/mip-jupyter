# Scratch workspace

Exploratory notebooks and scripts created during analysis sessions. **This folder
starts empty** in the repository; `stroke_preflight.py` syncs here from
`templates/scratch/` on container/local start (only if missing).

## Shipped into scratch at runtime

| File | Use |
|------|-----|
| `stroke_preflight.py` | SSR variable coverage gate — run first |

## Canonical examples (read or copy from `examples/`)

| File | Use |
|------|-----|
| `examples/algorithm_examples.py` | Pipeline method signatures — copy with `scratch-copy-template` |
| `examples/feres_analysis.ipynb` | Stroke territory analysis pattern |

## Cohort Scout kickoff prompt

```text
Exploration session on Stroke 3.7 / SSR.

Turn 1: scratch-list.
Run python scratch/stroke_preflight.py, then mip-algorithm-summary.
For novel work: scratch-copy-template scratch/<name>.py --source examples/algorithm_examples.py
and trim to one hypothesis. Max 20 lines per scratch edit.
End with primary OR (95% CI) and next human action.
```

## Recovery after tool-call formatting error

1. Start a **new chat**
2. `scratch-list` — resume the newest complete `scratch/<name>.py`
3. Continue with `scratch-append-lines` / `scratch-replace-snippet` only

See `docs/llm/wiki/agent-exploration.md` (via `read-guide --page agent-exploration`).
