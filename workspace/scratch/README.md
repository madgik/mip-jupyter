# Scratch workspace

Exploratory notebooks and scripts created during analysis sessions. **This folder starts empty** in the repository; only `stroke_preflight.py` and session Markdown templates sync here from `templates/scratch/` on container start (only if missing).

## Shipped into scratch at runtime

| File | Use |
|------|-----|
| `stroke_preflight.py` | SSR variable coverage gate — run first |
| `_session.template.md` → `_session.md` | Session objective (via `scratch-init`) |
| `_bottlenecks.template.md` → `_bottlenecks.md` | Bottleneck log (via `scratch-init`) |

## Canonical examples (read or copy from `examples/`)

| File | Use |
|------|-----|
| `examples/algorithm_examples.py` | Pipeline method signatures — copy with `scratch-copy-template` |
| `examples/feres_analysis.ipynb` | Stroke territory analysis pattern |

## Cohort Scout kickoff prompt

```text
Exploration session on Stroke 3.7 / SSR.

Turn 1: scratch-init, then scratch-list.
Run python scratch/stroke_preflight.py, then mip-algorithm-summary.
For novel work: scratch-copy-template scratch/<name>.py --source examples/algorithm_examples.py
and trim to one hypothesis. Max 20 lines per scratch edit.
Log each step with scratch-log-bottleneck.
End with primary OR (95% CI), top 5 bottlenecks, and next human action.
```

## Recovery after tool-call formatting error

1. Start a **new chat**
2. `scratch-list` — resume the newest complete `scratch/<name>.py`
3. Continue with `scratch-append-lines` / `scratch-replace-snippet` only

See `docs/llm/wiki/agent-exploration.md` (via `read-guide --page agent-exploration`).
