#!/usr/bin/env bash
# Operator acceptance gate for Cohort Scout shell guard + vLLM (no Jupyter UI required).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE_URL="${CODEX_VLLM_BASE_URL:-http://100.92.46.71:8001/v1}"
MODEL="${CODEX_VLLM_MODEL:-nemotron3-super-nvfp4}"

echo "Checking vLLM models at ${BASE_URL}..."
curl -fsS "${BASE_URL}/models" | grep -q "${MODEL}"

echo "Checking Responses API..."
curl -fsS "${BASE_URL}/responses" \
  -H 'Content-Type: application/json' \
  -d "{\"model\":\"${MODEL}\",\"input\":\"Reply with OK only.\",\"max_output_tokens\":256}" \
  | grep -q '"status"'

echo "Running shell guard and persona regression tests..."
cd "${ROOT}"
uv run pytest \
  mip_jupyter_dev/test_shell_guard.py \
  mip_jupyter_dev/test_codex_bootstrap.py \
  mip_jupyter_dev/test_stroke_federated.py \
  -q \
  -k "shell or tool_call_parse or vllm_unavailable or select_primary or coverage or format_logistic or parse_logistic"

echo "Acceptance gate passed."
echo "Manual UI check (optional): in JupyterLab chat, send:"
echo "  @Cohort Scout run a novel statistical stroke analysis with significance on SSR"
