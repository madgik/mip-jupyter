# Runtime State Protocol

**Read when:** You are continuing work after context compaction, using a handoff, handling a pivot/fork/reset, or adding/maintaining `.llm/` runtime state.

**Skip if:** The user only needs a one-shot answer or tiny edit and no existing runtime chat state is involved.

## Role of `.llm/`

`.llm/` is runtime memory from actual agent work. It augments static instructions; it does not replace `AGENTS.md` or this `docs/llm` playbook.

Keep this distinction:

- `AGENTS.md` - mandatory repo-level startup rules
- `docs/llm/` - static operating manual
- `.llm/` - runtime session/task memory
- `scratch/` - notebooks, experiments, temporary work

## Boot Order

1. Obey system/developer instructions.
2. Read `AGENTS.md`.
3. Read `docs/llm/INDEX.md`.
4. Read one relevant `docs/llm/wiki/` page.
5. Read `.llm/project.md` if present.
6. Read `.llm/chats/<chat_id>/state.md` if continuing a known chat.
7. Read `.llm/chats/<chat_id>/handoff.md` if present.
8. Read the active objective file listed in `state.md` if present.
9. Classify the current request.
10. Continue, simple-edit, pivot, fork, or reset.

Do not read everything by default. Read `journal.md`, `decisions.md`, `artifacts.md`, old objectives, and `archive/` only on demand.

## Request Classification

- **Simple edit:** small localized change; no new objective; minimal state update.
- **Continuation:** extends the current active objective.
- **Pivot with carry-over:** new goal, but prior context remains useful.
- **Fork:** side path without abandoning the old objective.
- **Hard reset:** explicit clean slate or start-over request.

Default to continuation for minor changes and pivot with carry-over for major goal changes. Use hard reset only when explicit.

For ambiguous pivots, ask exactly:

```text
Do you want this as a pivot that keeps useful context, or a hard reset where I archive the previous objective and start clean?
```

## State Files

- `state.md` is compact router state, not a transcript.
- `handoff.md` is a short transfer summary.
- `journal.md` is append-only history and is not read by default.
- `objective-*.md` tracks active/resumable work.

Update `state.md` only when objective, mode, status, plan, risk, next actions, verification status, or phase changes.

## Notebook And MIP Work

For simple notebook edits, inspect the outline or relevant cells, edit only requested cells, and run only affected cells when code changed. Do not run the whole notebook unless needed.

For long MIP/Jupyter/statistical workflows, use `analysis-long` mode and track data model, dataset IDs, variable IDs, filters, cohort definition, pipeline, experiment ID, polling status, notebook path, affected cells, execution status, and summarized results.

Never store secrets, token values, private connection strings, raw private data, or full sensitive notebook outputs in `.llm/`.

**Next file:** `.llm/README.md` when implementing or maintaining the protocol; otherwise the active `.llm/chats/<chat_id>/state.md` for the chat being resumed.
