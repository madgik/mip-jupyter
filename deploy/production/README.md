# Production deployment

Production Jupyter deployments are typically orchestrated by the MIP platform (Kubernetes + JupyterHub).

## Images

| Image | Dockerfile | Purpose |
|-------|------------|---------|
| Single-user notebook | `docker/singleuser/Dockerfile` | User JupyterLab server with pre-installed `mip` client |
| JupyterHub | `docker/hub/Dockerfile` | Hub that spawns single-user images |

Build from the repository root:

```bash
docker build -f docker/singleuser/Dockerfile -t mip-jupyter:latest .
docker build -f docker/hub/Dockerfile -t mip-jupyterhub:latest .
```

## Hub configuration

`docker/hub/jupyterhub_config.py` is a starting point for KubeSpawner settings (image name, backend URL, storage, resource limits). Override values for your cluster.

## User workspace

Spawned notebooks mount persistent storage at `/home/jovyan/work`. On first start, the single-user image seeds that directory from `/opt/mip-workspace-template/` when `Welcome.ipynb` is missing.

Users see only onboarding notebooks, examples, and docs — not deployment files or Python client source.

## Secrets

Inject `MIP_TOKEN` / `PLATFORM_TOKEN` and `PLATFORM_BACKEND_URL` via your orchestrator. Do not bake secrets into images.
