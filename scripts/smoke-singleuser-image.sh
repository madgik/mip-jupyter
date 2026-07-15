#!/usr/bin/env bash
# Smoke-test a built mip-jupyter single-user image (shell-bridge / Codex mode).
set -euo pipefail

IMAGE="${1:?Usage: $0 <image:tag>}"
CONTAINER="mip-jupyter-smoke-$$"
TOKEN="${SMOKE_TOKEN:-smoke}"
PORT="${SMOKE_PORT:-8888}"

cleanup() {
  docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker run -d --name "${CONTAINER}" -p "${PORT}:8888" \
  -e JUPYTER_TOKEN="${TOKEN}" \
  -e CODEX_VLLM_BASE_URL=http://127.0.0.1:9/v1 \
  -e CODEX_VLLM_MODEL=nemotron3-super-nvfp4 \
  "${IMAGE}"

echo "Waiting for Jupyter..."
curl --retry 60 --retry-delay 2 --retry-all-errors -fsS \
  "http://127.0.0.1:${PORT}/api/status?token=${TOKEN}" >/dev/null

docker exec "${CONTAINER}" sh -lc '
  test -x /tmp/mip-codex-home/bin/jupyter-mcp
  test -x /tmp/mip-codex-home/bin/mip-shell-guard
  test ! -f /tmp/mip-codex-home/bin/codex-acp || test -x /tmp/mip-codex-home/bin/codex-acp
  ! grep -q "\[mcp_servers" /tmp/mip-codex-home/config.toml
  test -f /home/jovyan/work/scratch/stroke_preflight.py
  grep -q "# %%" /home/jovyan/work/examples/algorithm_examples.py
'

docker exec "${CONTAINER}" python -m mip_jupyter_dev.jupyter_mcp_cli \
  --mcp-url http://127.0.0.1:3001/mcp \
  read-guide --page recipes/stroke-analysis --max-chars 500 >/dev/null

docker exec "${CONTAINER}" python -m mip_jupyter_dev.jupyter_mcp_cli \
  --mcp-url http://127.0.0.1:3001/mcp \
  notebook-outline workspace/examples/feres_analysis.ipynb >/dev/null

docker exec "${CONTAINER}" sh -lc '
  if /tmp/mip-codex-home/bin/mip-shell-guard -c "cat > scratch/foo.py << EOF"; then
    echo "shell guard should reject heredocs" >&2
    exit 1
  fi
'

echo "Smoke test passed for ${IMAGE}"
