# Workspace Guide

## Directory layout

```text
/home/jovyan/work/          (or workspace/ in local dev)
  Welcome.ipynb             Getting started
  examples/                 Canonical templates — copy before editing
  docs/                     User documentation (this folder)
  scratch/                  Your notebooks and experiments
```

## Examples vs scratch

| Location | Use for |
|----------|---------|
| `examples/` | Reference notebooks shipped with the platform. Read and learn from them. Copy into `scratch/` before making changes. |
| `scratch/` | Your own analysis work. Safe to create, edit, and delete freely. |

When an AI assistant creates a notebook without a path, it should default to `scratch/`.

## Saving and organizing work

- Use descriptive notebook names: `scratch/cohort_age_distribution.ipynb`.
- Keep exploratory drafts in `scratch/`; promote polished analyses by sharing with your team outside Jupyter if needed.
- Your `scratch/` content persists across sessions but may be subject to platform storage policies — check with your operator.

## Kernel tips

- **Restart kernel** after environment variable changes or package updates.
- **Run All** from the top when you change filters, variables, or preprocessing — downstream cells depend on earlier definitions.
- Large analyses can take time; each pipeline algorithm call is a round-trip to platform-backend.

## What is not in this workspace

- `mip` Python client source (`python-client/`) — installed as a package, not editable here.
- Deployment configuration — managed by your platform operator via `mip/deployment`.

## Related docs

- [Quickstart](quickstart.md)
- [API reference](api-reference.md)
- [Troubleshooting](troubleshooting.md)
