#!/bin/sh
set -eu

WORK="${MIP_WORK_DIR:-/home/jovyan/work}"
TEMPLATE="${MIP_WORKSPACE_TEMPLATE:-/opt/mip-workspace-template}"
MCP_PORT="${JUPYTER_MCP_PORT:-3001}"
JUPYTER_AI_CONFIG="${JUPYTER_AI_CONFIG:-/tmp/mip-jupyter-ai-config.json}"

mkdir -p "${WORK}/scratch"

if [ ! -f "${WORK}/Welcome.ipynb" ]; then
  cp -a "${TEMPLATE}/." "${WORK}/"
fi

mkdir -p "${WORK}/scratch"

export MIP_JUPYTER_ROOT="${WORK}"
export JUPYTER_MCP_URL="http://127.0.0.1:${MCP_PORT}/mcp"
python -m mip_jupyter_dev.jupyter_mcp_config "${JUPYTER_AI_CONFIG}" --mcp-port "${MCP_PORT}"

default_notebook="${MIP_NOTEBOOK:-Welcome.ipynb}"

exec jupyter lab \
  --no-browser \
  --ServerApp.ip="${JUPYTER_HOST:-0.0.0.0}" \
  --ServerApp.port="${JUPYTER_PORT:-8888}" \
  --ServerApp.token="${JUPYTER_TOKEN:-}" \
  --ServerApp.root_dir="${WORK}" \
  --ServerApp.default_url="/lab/tree/${default_notebook}" \
  --config "${JUPYTER_AI_CONFIG}"
