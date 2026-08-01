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
- `CODEX_VLLM_MODEL` (default `qwen36-nvfp4`)
- `CODEX_REASONING_EFFORT` (default `low`; use `medium` for exploration pods)
- Optional: `CODEX_VLLM_PROVIDER`, `CODEX_MODEL_CONTEXT_WINDOW`, `CODEX_AUTO_COMPACT_TOKEN_LIMIT`

Hub spawner configuration should inject backend URL and token at spawn time. See `docker/hub/jupyterhub_config.py` for the reference implementation.

Keep the Codex agent window at **131072** (default) even when vLLM serves
`max_model_len=262144`. Do not enable native Responses MCP for this stack; Cohort
Scout uses the shell bridge.

### Required vLLM serve profile (`qwen36-nvfp4`)

Serve `nvidia/Qwen3.6-35B-A3B-NVFP4` as id `qwen36-nvfp4` with:

- `--reasoning-parser qwen3`
- `--enable-auto-tool-choice`
- `--tool-call-parser qwen3_xml` (or `qwen3_coder` if `qwen3_xml` is unavailable)
- `--default-chat-template-kwargs '{"enable_thinking": false}'` for interactive Hub chat
- `--max-model-len 262144` (agent context stays capped at 131072 in Codex)
- `--gpu-memory-utilization 0.90` on the dedicated GPU box (more KV cache headroom; keep `max-num-seqs 1` for light concurrency)

Thinking on by default burns output budget on CoT before the final message. Codex
cannot pass `chat_template_kwargs` on the Responses path, so disable thinking at
serve time for default chat; use `CODEX_REASONING_EFFORT=medium` only on
exploration pods if you re-enable thinking server-side for those workloads.

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
