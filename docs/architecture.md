# Architecture

## Runtime flow

```text
Jupyter notebook (mip-jupyter image)
  → mip Python client (installed package)
  → platform-backend (/services)
  → Exaflow
```

Notebooks never call Exaflow directly.

## Repository roles

| Area | Audience | Contents |
|------|----------|----------|
| `workspace/` | Production Jupyter users | Welcome notebook, examples, user docs, scratch area |
| `python-client/` | Developers | `mip` package source and tests |
| `docker/` | Operators | Single-user and Hub image definitions |
| `deploy/` | Operators | Local Compose and production deployment notes |
| `mip_jupyter_dev/` | Local developers | JupyterLab runner with Codex/MCP for agent development |
| `docs/` | Operators and agents | Architecture, layout, release process, agent wiki |

## Production workspace model

The single-user Docker image:

1. Installs `mip` from `python-client/` as a Python package during build.
2. Copies `workspace/` to `/opt/mip-workspace-template/` inside the image.
3. On container start, seeds `/home/jovyan/work` from the template when `Welcome.ipynb` is absent.
4. Starts JupyterLab with root `/home/jovyan/work` and default URL `Welcome.ipynb`.

Deployment artifacts (Dockerfiles, Hub config, client source) are not copied into the user workspace.

## Local development

Developers run the full repository with `uv run mip-notebook`. The runner uses the repository root as Jupyter root so `python-client/` and tooling remain editable. Default notebooks live under `workspace/`.
