# Troubleshooting

## `Client.from_env()` fails or cannot connect

1. Confirm `PLATFORM_BACKEND_URL` (or `MIP_BASE_URL`) points at platform-backend under `/services`.
2. Confirm `MIP_TOKEN` (or `PLATFORM_TOKEN`) is set and not expired.
3. In JupyterHub deployments, the hub may inject `JUPYTERHUB_API_URL` and `JUPYTERHUB_API_TOKEN` for token refresh.

## Import errors (`import mip` fails)

The `mip` package is installed in the container image. If import fails, contact your platform operator — the Python client source is not part of this workspace.

## Backend validation errors

- Filter operators such as `contains`, `starts_with`, and `ends_with` may not be accepted by the backend validator.
- Check variable codes with `dm.variables.search("...")` before building filters.

## Notebook kernel issues

Restart the kernel after environment changes. If problems persist, restart the notebook server from JupyterHub.

## Where to save work

- Use `scratch/` for your own notebooks and experiments.
- Canonical examples under `examples/` are provided as templates; copy them into `scratch/` before editing if you want to keep the originals.

See [Workspace guide](workspace-guide.md) for details.

## Getting help

- Re-read [Quickstart](quickstart.md) and `Welcome.ipynb`.
- Ask your platform administrator for backend URL, token, and data-model access issues.
