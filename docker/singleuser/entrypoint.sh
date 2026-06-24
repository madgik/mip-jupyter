#!/bin/sh
set -eu

WORK="${MIP_WORK_DIR:-/home/jovyan/work}"
TEMPLATE="${MIP_WORKSPACE_TEMPLATE:-/opt/mip-workspace-template}"
MCP_PORT="${JUPYTER_MCP_PORT:-3001}"
JUPYTER_AI_CONFIG="${JUPYTER_AI_CONFIG:-/tmp/mip-jupyter-ai-config.json}"
CODEX_HOME="${CODEX_HOME:-/tmp/mip-codex-home}"

mkdir -p "${WORK}/scratch"

if [ ! -f "${WORK}/Welcome.ipynb" ]; then
  cp -a "${TEMPLATE}/." "${WORK}/"
fi

mkdir -p "${WORK}/scratch"

# Trust shipped notebooks so execution/output rendering is not blocked in Lab.
find "${WORK}" -name '*.ipynb' -exec jupyter trust {} + 2>/dev/null || true

export MIP_JUPYTER_ROOT="${WORK}"
export MIP_AGENT_DOCS="${MIP_AGENT_DOCS:-/opt/mip-agent-docs}"
export JUPYTER_MCP_URL="http://127.0.0.1:${MCP_PORT}/mcp"

if [ -n "${CODEX_VLLM_BASE_URL:-}" ]; then
  rm -rf "${CODEX_HOME}"
  python -m mip_jupyter_dev.codex_bootstrap "${CODEX_HOME}" "${JUPYTER_AI_CONFIG}" --mcp-port "${MCP_PORT}"
  export CODEX_HOME
  if [ -x "${CODEX_HOME}/bin/codex-acp" ]; then
    export PATH="${CODEX_HOME}/bin:${PATH}"
  fi
else
  python -m mip_jupyter_dev.jupyter_mcp_config "${JUPYTER_AI_CONFIG}" --mcp-port "${MCP_PORT}"
fi

default_notebook="${MIP_NOTEBOOK:-Welcome.ipynb}"

hub_args=""
if [ -n "${JUPYTERHUB_SERVICE_PREFIX:-}" ]; then
  hub_args="--ServerApp.base_url=${JUPYTERHUB_SERVICE_PREFIX}"
  default_url="lab/tree/${default_notebook}"
else
  default_url="/lab/tree/${default_notebook}"
fi

exec jupyter lab \
  --no-browser \
  --ServerApp.ip="${JUPYTER_HOST:-0.0.0.0}" \
  --ServerApp.port="${JUPYTER_PORT:-8888}" \
  --ServerApp.token="${JUPYTER_TOKEN:-}" \
  --ServerApp.root_dir="${WORK}" \
  --ServerApp.default_url="${default_url}" \
  ${hub_args} \
  --YDocExtension.disable_rtc=True \
  --ServerApp.websocket_ping_interval=30000 \
  --ServerApp.websocket_ping_timeout=30000 \
  --config "${JUPYTER_AI_CONFIG}"
