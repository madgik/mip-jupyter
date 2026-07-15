# Jupyter AI Codex Prototype

This prototype adds Jupyter AI to the local JupyterLab workflow so developers can test a vLLM-backed Codex assistant. The repository does not include personal credentials or tokens.

Jupyter AI v3 discovers ACP-compatible agents from the runtime environment. The local runner starts JupyterLab with a temporary Codex configuration that points Cohort Scout at a vLLM Responses-compatible `/v1/responses` endpoint and the `nemotron3-super-nvfp4` model.

Architecture overview and Mermaid source: [jupyter-ai-architecture.md](jupyter-ai-architecture.md).

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

The vLLM Codex workflow uses a temporary `CODEX_HOME` containing `config.toml` and `model-catalog.json`:

```toml
model = "nemotron3-super-nvfp4"
model_provider = "vllm"
model_catalog_json = "/tmp/mip-codex-home-.../model-catalog.json"
model_context_window = 131072
model_auto_compact_token_limit = 112000
model_reasoning_effort = "medium"
model_reasoning_summary = "none"
model_supports_reasoning_summaries = false
approval_policy = "never"
sandbox_mode = "danger-full-access"
model_verbosity = "low"
web_search = "disabled"

[features]
multi_agent = false

[model_providers.vllm]
name = "vLLM"
base_url = "http://100.92.46.71:8001/v1"
wire_api = "responses"
```

The generated model catalog contains only `nemotron3-super-nvfp4` with a 131072-token context window. Catalog metadata intentionally keeps the Responses payload compatible with the current vLLM shim by setting `support_verbosity` to `false`, `apply_patch_tool_type` to `null`, `supports_parallel_tool_calls` to `false`, and `use_responses_lite` to `true`.

The runner also prepends a generated `codex-acp` wrapper to `PATH`. The wrapper passes `-c approval_policy="never"`, `-c sandbox_mode="danger-full-access"`, and `-c shell_environment_policy.inherit="all"` directly to `codex-acp`; this is needed because the ACP process otherwise starts Codex with `on-request` approvals and a read-only sandbox even when the temporary `config.toml` contains the desired values.

If the vLLM endpoint is unavailable during a chat request, Cohort Scout catches the likely ACP/Codex connection error and replies with a short service-unavailable message instead of exposing a raw traceback to the user.

The runner starts a curated Jupyter MCP wrapper server by default. Shell-bridge
mode does not emit `builtin_mcp_servers` or a Codex `[mcp_servers]` section, so it
does not forward that server as native Responses `mcp` tools to vLLM. The
current vLLM Responses shim rejects native `mcp` and `web_search_preview` tool
payloads with `Object of type Undefined is not JSON serializable`.

Instead, Codex receives `JUPYTER_MCP_URL` and model instructions to call the MCP server through the shell bridge:

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli create-notebook scratch/mcp_probe.ipynb
python -m mip_jupyter_dev.jupyter_mcp_cli append-markdown scratch/mcp_probe.ipynb "MCP OK"
```

The bridge still calls the Jupyter MCP server; it just avoids sending a native
Responses `mcp` tool type to vLLM. Native MCP forwarding can be enabled with
`CODEX_ENABLE_NATIVE_JUPYTER_MCP=1` only for providers that support Responses
MCP tools. When native forwarding is enabled, the generated Codex config includes
the MCP server and the model instructions allow native MCP calls.

Restart JupyterLab after installing or changing agent binaries so Jupyter AI can rediscover available agents.

To use a different vLLM endpoint for local testing:

```bash
CODEX_VLLM_BASE_URL=http://127.0.0.1:8001/v1 uv run mip-notebook
```

If the shell bridge regresses, native MCP forwarding should remain disabled for vLLM. Verify the MCP server directly with:

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli notebook-outline workspace/examples/feres_analysis.ipynb
```

For parallel local JupyterLab instances, use a different JupyterLab port. The runner chooses a free MCP port automatically unless `JUPYTER_MCP_PORT` or `--mcp-port` is set:

```bash
JUPYTER_PORT=8892 uv run mip-notebook
```

## Check the vLLM endpoint

From a machine connected to the same Tailscale network:

```bash
curl http://100.92.46.71:8001/v1/models
```

Expected model IDs include:

```text
nemotron3-super-nvfp4
```

The local and Hub runners use `nemotron3-super-nvfp4`.

The endpoint must support the Responses API path used by Codex:

```bash
curl http://100.92.46.71:8001/v1/responses \
  -H 'Content-Type: application/json' \
  -d '{"model":"nemotron3-super-nvfp4","input":"Say OK only","max_output_tokens":256}'
```

`nemotron3-super-nvfp4` may emit reasoning tokens before the final message; use a large enough `max_output_tokens` value in manual curl tests.

## Agent Onboarding

Jupyter AI Codex is steered by a layered wiki instead of ad-hoc repo exploration:

- **Production Codex:** `read-guide` reads the default workspace guide or an allowlisted routed page from `/opt/mip-agent-docs/`; `search-docs` searches user docs in workspace `docs/`.
- [`AGENTS.md`](../AGENTS.md) — repository bootstrap entry point for Cursor and IDE agents
- [`docs/llm/INDEX.md`](../docs/llm/INDEX.md) — wiki map and task routing table
- [`docs/user/`](../docs/user/) — canonical user documentation (shipped to workspace `docs/`)

The notebook runner injects slim `base_instructions` in the generated Codex model catalog that point production agents at the routed wiki and curated MCP tools only when those sources are needed.

In shell-bridge mode, those instructions require Cohort Scout to use
`jupyter_mcp_cli` for notebook and MIP tool actions; native `mcp__*` tools are
disabled for vLLM. For substantial or multi-step workflows only, the agent
may validate the analysis in a temporary Python file before transferring it to
notebook cells.

The production single-user image seeds `workspace/` and `docs/user/` into `/home/jovyan/work`, bundles agent wiki at `/opt/mip-agent-docs/`, and does not copy client source into the user file browser.

## Verify Jupyter AI and Codex

1. Open JupyterLab.
2. Open the chat panel from the left sidebar, or create a chat from the launcher.
3. Type `@` in the chat input and verify that **Cohort Scout** appears in the persona menu.
   Stock Jupyter AI ACP personas such as Codex, Claude, and Copilot are hidden; Cohort Scout is the only available persona.
4. Use one of the existing notebooks as context, for example `workspace/examples/feres_analysis.ipynb` or `workspace/Welcome.ipynb`.
5. Send one of these prompts:

```text
@Cohort Scout explain the structure of this workspace.
@Cohort Scout inspect workspace/Welcome.ipynb and summarize what a new MIP user should do first.
@Cohort Scout explain how mip.Client.from_env() gets configuration.
@Cohort Scout create a new scratch notebook named mcp_probe.ipynb with one markdown cell that says MCP OK.
```

The current prototype is considered successful if the Jupyter AI chat UI opens, Cohort Scout appears after the runtime agent setup, it can answer against an existing notebook or workspace file, and it can use the Jupyter MCP shell bridge to create or edit a notebook without any credentials committed to the repository.

### Golden prompts (context efficiency)

Use these prompts to verify that Cohort Scout follows the wiki instead of grepping the full repo. Success means a correct answer with **at most three targeted file reads** before replying (no broad `find` or repo-wide `grep` on startup).

| Prompt | Expected reads |
|--------|----------------|
| `@Cohort Scout explain how mip.Client.from_env() gets configuration` | `read-guide --page 05-env-and-backend --topic "Client.from_env"` |
| `@Cohort Scout summarize what a new MIP user should do first` | `read-guide --page 01-onboarding` and optionally `workspace/Welcome.ipynb` outline |
| `@Cohort Scout create a new scratch notebook named mcp_probe.ipynb with one markdown cell that says MCP OK` | MCP CLI only; use `read-guide --page 04-jupyter-mcp` if command details are needed |
| `@Cohort Scout run a novel statistical stroke analysis with significance on SSR` | `read-guide --page recipes/stroke-analysis --topic novel`; `mip-data-model-summary stroke --version 3.7`; `python scratch/stroke_preflight.py`; `scratch-copy-template scratch/<name>.py --source examples/algorithm_examples.py`; small `scratch-append-lines` / `scratch-replace-snippet` edits; run script; `scratch-to-notebook`; no heredocs |

Success for the stroke prompt means: bounded metadata discovery, SSR-only dataset (no SSR+even/odd mix), preflight coverage check, a **new** scratch script derived from `examples/algorithm_examples.py` (trimmed to one hypothesis), federated `describe` / `t_test` / `chi_square_test` / `logistic_regression` (no `Pipeline.run()`), primary adjusted logistic **OR (95% CI)** on the OR scale, a populated `scratch/<name>.ipynb`, aggregate results only, and no giant shell payloads or raw row extraction.

## Image smoke test (operators)

After building the single-user image, run:

```bash
scripts/smoke-singleuser-image.sh hbpmip/mip-jupyter:<tag>
```

The script checks Jupyter status, Codex/jupyter-mcp wrappers, shell-bridge config (no native `[mcp_servers]`), `read-guide --page`, and `notebook-outline`.

For vLLM and parse-error acceptance (no UI):

```bash
scripts/accept-cohort-scout-vllm.sh
```

After deploying a new image tag, recreate existing single-user pods so they pull the updated image; `imagePullPolicy` alone does not refresh already-running pods.

## Production Notes

This prototype is a local development workflow. Do not treat it as a production JupyterHub rollout.

Before enabling AI agents in shared Hub environments, review:

- where temporary Codex runtime state is stored
- whether agents can read other users' files or mounted secrets
- command execution and approval behavior
- network egress and model-provider policy
- audit logging and support expectations
