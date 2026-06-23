# Jupyter AI Codex Prototype

This prototype adds Jupyter AI to the local JupyterLab workflow so developers can test a Codex-backed assistant. The repository does not include personal credentials, ChatGPT session files, OpenAI API keys, or tokens.

Jupyter AI v3 discovers ACP-compatible agents from the runtime environment. The local runner starts JupyterLab with a temporary Codex configuration that points Codex at the North vLLM OpenAI-compatible `/v1/responses` endpoint.

References:

- Codex CLI: https://developers.openai.com/codex/cli
- Codex CLI README: https://github.com/openai/codex

## Run JupyterLab

From the repository root:

```bash
uv sync
uv run mip-notebook
```

Open:

```text
http://127.0.0.1:8888/lab/tree/workspace/examples/feres_analysis.ipynb?token=dev
```

## Install Codex ACP

Install the Codex CLI and confirm the executable is available:

```bash
npm install -g @openai/codex
codex --version
```

Install the Codex ACP adapter required by Jupyter AI:

```bash
npm install -g @zed-industries/codex-acp
```

The local North vLLM provider does not require `codex login` or an OpenAI API key. The runner sets `CODEX_HOME` to a temporary directory containing `config.toml` and `model-catalog.json`:

```toml
model = "North-Mini-Code-1.0"
model_provider = "north_vllm"
model_catalog_json = "/tmp/mip-codex-home-.../model-catalog.json"
model_context_window = 131072
model_auto_compact_token_limit = 100000
model_reasoning_effort = "minimal"
model_reasoning_summary = "none"
model_supports_reasoning_summaries = false
approval_policy = "never"
sandbox_mode = "danger-full-access"
model_verbosity = "low"
web_search = "disabled"

[features]
multi_agent = false

[model_providers.north_vllm]
name = "North vLLM"
base_url = "http://100.92.46.71:8001/v1"
wire_api = "responses"
```

The generated model catalog adds explicit metadata for `North-Mini-Code-1.0`, including the 131072-token context window. It intentionally keeps the Responses payload compatible with the current vLLM shim by setting `support_verbosity` to `false`, `apply_patch_tool_type` to `null`, `supports_parallel_tool_calls` to `false`, and `use_responses_lite` to `true`.

The runner also prepends a generated `codex-acp` wrapper to `PATH`. The wrapper passes `-c approval_policy="never"`, `-c sandbox_mode="danger-full-access"`, and `-c shell_environment_policy.inherit="all"` directly to `codex-acp`; this is needed because the ACP process otherwise starts Codex with `on-request` approvals and a read-only sandbox even when the temporary `config.toml` contains the desired values.

The runner starts a curated Jupyter MCP wrapper server by default. It does not forward that server as native Responses `mcp` tools to Codex when using North vLLM, because the current vLLM Responses shim rejects native `mcp` and `web_search_preview` tool payloads with `Object of type Undefined is not JSON serializable`.

Instead, Codex receives `JUPYTER_MCP_URL` and model instructions to call the MCP server through the shell bridge:

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli create-notebook mcp_probe.ipynb
python -m mip_jupyter_dev.jupyter_mcp_cli add-markdown mcp_probe.ipynb "MCP OK"
```

The bridge still calls the Jupyter MCP server; it just avoids sending a native Responses `mcp` tool type to North vLLM. Native MCP forwarding can be enabled with `CODEX_ENABLE_NATIVE_JUPYTER_MCP=1` only for providers that support Responses MCP tools.

Restart JupyterLab after installing or changing agent binaries so Jupyter AI can rediscover available agents.

To use a different endpoint for local testing:

```bash
CODEX_VLLM_BASE_URL=http://127.0.0.1:8001/v1 uv run mip-notebook
```

If the shell bridge regresses, native MCP forwarding should remain disabled for North vLLM. Verify the MCP server directly with:

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli read-notebook workspace/examples/feres_analysis.ipynb
```

For parallel local JupyterLab instances, use a different JupyterLab port. The runner chooses a free MCP port automatically unless `JUPYTER_MCP_PORT` or `--mcp-port` is set:

```bash
JUPYTER_PORT=8892 uv run mip-notebook
```

## Check the North vLLM Endpoint

From a machine connected to the same Tailscale network:

```bash
curl http://100.92.46.71:8001/v1/models
```

Expected model ID:

```text
North-Mini-Code-1.0
```

The endpoint must support the Responses API path used by Codex:

```bash
curl http://100.92.46.71:8001/v1/responses \
  -H 'Content-Type: application/json' \
  -d '{"model":"North-Mini-Code-1.0","input":"Say OK","max_output_tokens":128}'
```

## Agent Onboarding

Jupyter AI Codex is steered by a layered wiki instead of ad-hoc repo exploration:

- [`AGENTS.md`](../AGENTS.md) — bootstrap entry point (scope, routing, guardrails)
- [`docs/llm/INDEX.md`](../docs/llm/INDEX.md) — wiki map and task routing table
- [`docs/llm/wiki/`](../docs/llm/wiki/) — task-scoped pages (onboarding, workflow, API cheat sheet, MCP, env)

The notebook runner injects slim `base_instructions` in the generated Codex model catalog that point agents at `AGENTS.md` and the wiki before exploring files.

The production single-user image (`docker/singleuser/Dockerfile`) seeds `workspace/` into `/home/jovyan/work` and does not copy deployment or client source into the user file browser. Local development uses the full repository checkout with agent wiki under `docs/llm/`.

## Verify Jupyter AI and Codex

1. Open JupyterLab.
2. Open the chat panel from the left sidebar, or create a chat from the launcher.
3. Type `@` in the chat input and verify that Codex appears in the persona menu.
4. Use one of the existing notebooks as context, for example `workspace/examples/feres_analysis.ipynb` or `workspace/Welcome.ipynb`.
5. Send one of these prompts:

```text
@Codex explain the structure of this workspace.
@Codex inspect workspace/Welcome.ipynb and summarize what a new MIP user should do first.
@Codex explain how mip.Client.from_env() gets configuration.
@Codex create a new notebook named mcp_probe.ipynb with one markdown cell that says MCP OK.
```

The current prototype is considered successful if the Jupyter AI chat UI opens, Codex appears after the runtime agent setup, Codex can answer against an existing notebook or workspace file, and Codex can use the Jupyter MCP shell bridge to create or edit a notebook without any credentials committed to the repository.

### Golden prompts (context efficiency)

Use these prompts to verify that Codex follows the wiki instead of grepping the full repo. Success means a correct answer with **at most three targeted file reads** before replying (no broad `find` or repo-wide `grep` on startup).

| Prompt | Expected reads |
|--------|----------------|
| `@Codex explain how mip.Client.from_env() gets configuration` | `docs/llm/wiki/05-env-and-backend.md` or `python-client/mip/client.py` |
| `@Codex summarize what a new MIP user should do first` | `docs/llm/wiki/01-onboarding.md` and optionally `workspace/Welcome.ipynb` |
| `@Codex create a new notebook named mcp_probe.ipynb with one markdown cell that says MCP OK` | MCP CLI only per `docs/llm/wiki/04-jupyter-mcp.md` |

## Production Notes

This prototype is a local development workflow. Do not treat it as a production JupyterHub rollout.

Before enabling AI agents in shared Hub environments, review:

- where user credentials and Codex auth caches are stored if non-local providers are enabled
- whether agents can read other users' files or mounted secrets
- command execution and approval behavior
- network egress and model-provider policy
- audit logging and support expectations
