#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install uv, then run this script again." >&2
  exit 1
fi

if ! command -v codex-acp >/dev/null 2>&1; then
  echo "codex-acp is required for Jupyter AI Codex." >&2
  echo "Install it with: npm install -g @zed-industries/codex-acp" >&2
  exit 1
fi

export PLATFORM_BACKEND_URL="${PLATFORM_BACKEND_URL:-http://127.0.0.1:8080/services}"
export CODEX_VLLM_BASE_URL="${CODEX_VLLM_BASE_URL:-http://100.92.46.71:8001/v1}"
export CODEX_VLLM_MODEL="nemotron3-super-nvfp4"
export JUPYTER_HOST="${JUPYTER_HOST:-127.0.0.1}"
export JUPYTER_PORT="${JUPYTER_PORT:-8888}"
export JUPYTER_TOKEN="${JUPYTER_TOKEN:-dev}"
export MIP_NOTEBOOK="${MIP_NOTEBOOK:-workspace/examples/feres_analysis.ipynb}"

echo "Starting mip-jupyter with vLLM Codex (${CODEX_VLLM_MODEL})"
echo "Codex vLLM endpoint: ${CODEX_VLLM_BASE_URL}"
echo "Jupyter URL: http://${JUPYTER_HOST}:${JUPYTER_PORT}/lab/tree/${MIP_NOTEBOOK}?token=${JUPYTER_TOKEN}"

exec uv run mip-notebook "$@"
