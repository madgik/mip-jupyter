#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install uv, then run this script again." >&2
  exit 1
fi

if ! command -v codex >/dev/null 2>&1; then
  echo "codex is required for normal OpenAI Codex." >&2
  echo "Install it with: npm install -g @openai/codex" >&2
  exit 1
fi

if ! command -v codex-acp >/dev/null 2>&1; then
  echo "codex-acp is required for Jupyter AI Codex." >&2
  echo "Install it with: npm install -g @zed-industries/codex-acp" >&2
  exit 1
fi

if ! codex login status >/dev/null 2>&1; then
  echo "Codex is not logged in." >&2
  echo "Run one of:" >&2
  echo "  codex login --device-auth" >&2
  echo "  printenv OPENAI_API_KEY | codex login --with-api-key" >&2
  exit 1
fi

choose_mcp_port() {
  python3 - "$1" "$2" <<'PY'
import errno
import socket
import sys

host = sys.argv[1]
preferred = int(sys.argv[2])


def is_free(port: int) -> bool:
    checked = False
    try:
        infos = socket.getaddrinfo(host or None, port, type=socket.SOCK_STREAM, flags=socket.AI_PASSIVE)
    except OSError:
        return False
    for family, socktype, proto, _canonname, sockaddr in set(infos):
        sock = socket.socket(family, socktype, proto)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            if family == socket.AF_INET6 and hasattr(socket, "IPPROTO_IPV6"):
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, True)
            sock.bind(sockaddr)
            checked = True
        except OSError as exc:
            if exc.errno == errno.EADDRNOTAVAIL:
                continue
            return False
        finally:
            sock.close()
    return checked


for candidate in range(preferred, preferred + 100):
    if is_free(candidate):
        print(candidate)
        raise SystemExit(0)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
}

JUPYTER_HOST="${JUPYTER_HOST:-127.0.0.1}"
JUPYTER_PORT="${JUPYTER_PORT:-8888}"
JUPYTER_TOKEN="${JUPYTER_TOKEN:-dev}"
if [[ -n "${MIP_JUPYTER_ROOT:-}" ]]; then
  JUPYTER_ROOT="$(cd "${MIP_JUPYTER_ROOT}" && pwd)"
else
  JUPYTER_ROOT="${PWD}"
fi
WORKSPACE_ROOT="$(cd "${PWD}/workspace" && pwd)"
if [[ -n "${MIP_NOTEBOOK:-}" ]]; then
  MIP_NOTEBOOK="${MIP_NOTEBOOK}"
elif [[ "${JUPYTER_ROOT}" == "${WORKSPACE_ROOT}" ]]; then
  MIP_NOTEBOOK="Welcome.ipynb"
else
  MIP_NOTEBOOK="workspace/examples/feres_analysis.ipynb"
fi
PLATFORM_BACKEND_URL="${PLATFORM_BACKEND_URL:-http://127.0.0.1:8080/services}"
CODEX_MODEL="${CODEX_MODEL:-gpt-5.5}"

if [[ -z "${JUPYTER_MCP_PORT:-}" ]]; then
  JUPYTER_MCP_PORT="$(choose_mcp_port localhost 3001)"
fi

TMP_DIR="$(mktemp -d -t mip-normal-codex-XXXXXX)"
cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

REAL_CODEX_ACP="$(command -v codex-acp)"
export REAL_CODEX_ACP
mkdir -p "${TMP_DIR}/bin"
cat >"${TMP_DIR}/bin/codex-acp" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
exec "${REAL_CODEX_ACP}" \
  -c "model=\"${CODEX_MODEL}\"" \
  -c 'shell_environment_policy.inherit="all"' \
  "$@"
SH
chmod 755 "${TMP_DIR}/bin/codex-acp"

JUPYTER_CONFIG="${TMP_DIR}/jupyter_ai_codex_openai.json"
cat >"${JUPYTER_CONFIG}" <<JSON
{
  "PersonaManager": {
    "default_persona_id": "jupyter-ai-personas::jupyter_ai_acp_client::CodexAcpPersona"
  },
  "MCPExtensionApp": {
    "mcp_port": ${JUPYTER_MCP_PORT}
  }
}
JSON

export PATH="${TMP_DIR}/bin:${PATH}"
export PLATFORM_BACKEND_URL
export CODEX_MODEL
unset CODEX_HOME

echo "Starting mip-jupyter with normal Codex (${CODEX_MODEL})"
echo "Using Codex auth and approval settings from your normal ~/.codex login/config"
echo "Jupyter MCP port: ${JUPYTER_MCP_PORT}"
echo "Jupyter root: ${JUPYTER_ROOT}"
echo "Jupyter URL: http://${JUPYTER_HOST}:${JUPYTER_PORT}/lab/tree/${MIP_NOTEBOOK}?token=${JUPYTER_TOKEN}"

uv run python -m jupyterlab --no-browser \
  --ServerApp.ip="${JUPYTER_HOST}" \
  --ServerApp.port="${JUPYTER_PORT}" \
  --ServerApp.token="${JUPYTER_TOKEN}" \
  --ServerApp.root_dir="${JUPYTER_ROOT}" \
  --ServerApp.default_url="/lab/tree/${MIP_NOTEBOOK}" \
  --config "${JUPYTER_CONFIG}" \
  "$@"
