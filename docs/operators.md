# Operators

Deployment and runtime orchestration for MIP Jupyter live in the **`mip/deployment`** repository, not in mip-jupyter.

## What mip-jupyter provides

| Deliverable | Location |
|-------------|----------|
| Single-user Jupyter image | `docker/singleuser/Dockerfile` |
| JupyterHub image and config | `docker/hub/` |
| `mip` Python client | `python-client/` (installed in images) |
| User workspace template | `workspace/` + `docs/user/` → `/home/jovyan/work` |
| Agent wiki (not user-visible) | `docs/llm/` + `AGENTS.md` → `/opt/mip-agent-docs/` |

## Environment contract

Notebooks and the `mip` client expect:

- `PLATFORM_BACKEND_URL` or `MIP_BASE_URL` — backend URL ending in `/services`
- `MIP_TOKEN` or `PLATFORM_TOKEN` — bearer token for platform-backend
- Optional: `JUPYTERHUB_API_URL`, `JUPYTERHUB_API_TOKEN` for hub-side token refresh

When Cohort Scout / vLLM is enabled, Hub spawners also pass:

- `CODEX_VLLM_BASE_URL` (required to bootstrap Codex)
- `CODEX_VLLM_MODEL` (default `nemotron3-super-nvfp4`)
- `CODEX_REASONING_EFFORT` (default `low`; use `medium` for exploration pods)
- Optional: `CODEX_VLLM_PROVIDER`, `CODEX_MODEL_CONTEXT_WINDOW`, `CODEX_AUTO_COMPACT_TOKEN_LIMIT`

Hub spawner configuration should inject backend URL and token at spawn time. See `docker/hub/jupyterhub_config.py` for the reference implementation.

## Image build and release

```bash
docker build -f docker/singleuser/Dockerfile -t mip-jupyter:<tag> .
docker build -f docker/hub/Dockerfile -t mip-jupyterhub:<tag> .
```

Full checklist: [`release-process.md`](release-process.md).

## Where to configure production

- **Compose / Kubernetes / Helm** — `mip/deployment`
- **Image tags in Hub** — update `JUPYTER_SINGLEUSER_IMAGE` in deployment values or `docker/hub/jupyterhub_config.py`
- **Keycloak / auth** — `mip/deployment` (Hub uses Keycloak when `KEYCLOAK_CLIENT_ID` is set)
- **Platform token refresh** — Hub `platform_token_service.py`; validate in deployment integration tests

## Smoke test after rollout

1. User logs in via Hub and lands on `Welcome.ipynb`.
2. `import mip` and `mip.Client.from_env()` succeed.
3. File browser shows `Welcome.ipynb`, `examples/`, `docs/`, `scratch/` only.
4. `docs/llm/` and `python-client/` are **not** visible to users.
5. Jupyter AI agents can call `agent_read_guide` (reads `/opt/mip-agent-docs/`).
