# Repository layout

```text
mip-jupyter/
  README.md

  docker/
    singleuser/
      Dockerfile          # Production single-user Jupyter image
      entrypoint.sh       # Seeds workspace and starts JupyterLab
    hub/
      Dockerfile          # JupyterHub image
      jupyterhub_config.py

  deploy/
    local/
      docker-compose.yml
      .env.example
    production/
      README.md

  python-client/
    mip/                  # Installed as package in production images
    tests/
    pyproject.toml

  workspace/              # Template copied into /home/jovyan/work in production
    Welcome.ipynb
    examples/
      feres_analysis.ipynb
    docs/
      mip-client-quickstart.md
      mip-client-api.md
      troubleshooting.md
    scratch/

  docs/
    architecture.md
    repository-layout.md
    release-process.md
    llm/                  # Agent onboarding wiki (developers)

  mip_jupyter_dev/        # Local dev runner (not in production workspace)
  expected_library.md     # API contract for client development
```

## What production users see

```text
/home/jovyan/work/
  Welcome.ipynb
  examples/
  docs/
  scratch/
```

## What production users do not see

- `python-client/` source tree
- Dockerfiles and Hub configuration
- `mip_jupyter_dev/` tooling
- Repository CI and deployment files

## Legacy root paths

Root-level `Dockerfile.jupyter` and `Dockerfile.jupyterhub` were moved to `docker/singleuser/` and `docker/hub/`. Update build scripts and CI to use the new paths.
