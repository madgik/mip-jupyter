"""Start local JupyterLab with Codex configured for mip-jupyter."""

from __future__ import annotations

import argparse
import errno
import json
import os
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path


DEFAULT_BACKEND_URL = "http://127.0.0.1:8080/services"
DEFAULT_TOKEN = "dev"
DEFAULT_NOTEBOOK = "workspace/examples/feres_analysis.ipynb"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8888
DEFAULT_MCP_PORT = 3001
DEFAULT_CODEX_BASE_URL = "http://100.92.46.71:8001/v1"
DEFAULT_CODEX_MODEL = "North-Mini-Code-1.0"
DEFAULT_CODEX_PROVIDER = "north_vllm"
DEFAULT_CODEX_CONTEXT_WINDOW = 131072
DEFAULT_CODEX_AUTO_COMPACT_LIMIT = 100000
DEFAULT_CODEX_PERSONA_ID = "jupyter-ai-personas::jupyter_ai_acp_client::CodexAcpPersona"
SAFE_JUPYTER_MCP_TOOLS = [
    "mip_jupyter_dev.jupyter_mcp_tools:create_notebook",
    "mip_jupyter_dev.jupyter_mcp_tools:add_markdown_cell",
    "mip_jupyter_dev.jupyter_mcp_tools:add_code_cell",
    "mip_jupyter_dev.jupyter_mcp_tools:edit_cell_by_index",
    "mip_jupyter_dev.jupyter_mcp_tools:read_notebook_cells",
    "mip_jupyter_dev.jupyter_mcp_tools:open_file",
    "mip_jupyter_dev.jupyter_mcp_tools:run_all_cells",
]


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _is_port_free(host: str, port: int) -> bool:
    checked_any_address = False
    try:
        addr_infos = socket.getaddrinfo(
            host or None,
            port,
            type=socket.SOCK_STREAM,
            flags=socket.AI_PASSIVE,
        )
    except OSError:
        return False
    for family, socktype, proto, _canonname, sockaddr in set(addr_infos):
        try:
            sock = socket.socket(family, socktype, proto)
        except OSError:
            continue
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            if family == socket.AF_INET6 and hasattr(socket, "IPPROTO_IPV6"):
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, True)
            sock.bind(sockaddr)
            checked_any_address = True
        except OSError as exc:
            if exc.errno == errno.EADDRNOTAVAIL:
                continue
            return False
        finally:
            sock.close()
    return checked_any_address


def _choose_mcp_port(host: str = "localhost", preferred: int = DEFAULT_MCP_PORT) -> int:
    for port in range(preferred, preferred + 100):
        if _is_port_free(host, port):
            return port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Start local JupyterLab for mip-jupyter.")
    parser.add_argument("--notebook", default=os.getenv("MIP_NOTEBOOK", DEFAULT_NOTEBOOK))
    parser.add_argument("--host", default=os.getenv("JUPYTER_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.getenv("JUPYTER_PORT", str(DEFAULT_PORT))))
    parser.add_argument(
        "--mcp-port",
        type=int,
        default=int(os.getenv("JUPYTER_MCP_PORT")) if os.getenv("JUPYTER_MCP_PORT") else None,
        help="MCP port for Jupyter tools. Defaults to the first free local port at or above 3001.",
    )
    parser.add_argument("--token", default=os.getenv("JUPYTER_TOKEN", DEFAULT_TOKEN))
    parser.add_argument("--codex-base-url", default=os.getenv("CODEX_VLLM_BASE_URL", DEFAULT_CODEX_BASE_URL))
    parser.add_argument("--codex-model", default=os.getenv("CODEX_VLLM_MODEL", DEFAULT_CODEX_MODEL))
    parser.add_argument("--codex-provider", default=os.getenv("CODEX_VLLM_PROVIDER", DEFAULT_CODEX_PROVIDER))
    parser.add_argument(
        "--codex-context-window",
        type=int,
        default=int(os.getenv("CODEX_MODEL_CONTEXT_WINDOW", str(DEFAULT_CODEX_CONTEXT_WINDOW))),
    )
    parser.add_argument(
        "--codex-auto-compact-limit",
        type=int,
        default=int(os.getenv("CODEX_AUTO_COMPACT_TOKEN_LIMIT", str(DEFAULT_CODEX_AUTO_COMPACT_LIMIT))),
    )
    parser.add_argument(
        "--disable-jupyter-mcp",
        action="store_true",
        default=_env_flag("CODEX_DISABLE_NATIVE_JUPYTER_MCP"),
        help="Disable native MCP forwarding to Codex. This is the default for North vLLM.",
    )
    parser.add_argument(
        "--enable-native-jupyter-mcp",
        action="store_true",
        default=_env_flag("CODEX_ENABLE_NATIVE_JUPYTER_MCP"),
        help="Forward Jupyter MCP as native Responses MCP tools. Do not use with North vLLM.",
    )
    return parser


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _write_codex_model_catalog(path: Path, args: argparse.Namespace) -> None:
    catalog = {
        "models": [
            {
                "slug": args.codex_model,
                "display_name": args.codex_model,
                "description": "Local North Mini Code model served by vLLM for mip-jupyter.",
                "default_reasoning_level": "minimal",
                "supported_reasoning_levels": [
                    {
                        "effort": "minimal",
                        "description": "Fast local inference with minimal reasoning.",
                    },
                    {
                        "effort": "low",
                        "description": "Light reasoning for local coding and notebook assistance.",
                    },
                ],
                "shell_type": "shell_command",
                "visibility": "list",
                "supported_in_api": True,
                "priority": 0,
                "additional_speed_tiers": [],
                "service_tiers": [],
                "availability_nux": None,
                "upgrade": None,
                "base_instructions": (
                    "You are Codex in JupyterLab via Jupyter AI. Before exploring the repo, "
                    "read AGENTS.md and docs/llm/INDEX.md; follow the task routing table. "
                    "Do not grep or list the full tree on startup. Keep edits focused. "
                    "For notebook create/edit use python -m mip_jupyter_dev.jupyter_mcp_cli "
                    "(JUPYTER_MCP_URL is set); see docs/llm/wiki/04-jupyter-mcp.md. "
                    "After edits run read-notebook to verify. Do not ask the user to paste "
                    "notebook cells manually."
                ),
                "supports_reasoning_summaries": False,
                "default_reasoning_summary": "none",
                "support_verbosity": False,
                "default_verbosity": "low",
                "apply_patch_tool_type": None,
                "web_search_tool_type": "text_and_image",
                "truncation_policy": {"mode": "tokens", "limit": 10000},
                "supports_parallel_tool_calls": False,
                "supports_image_detail_original": False,
                "context_window": args.codex_context_window,
                "max_context_window": args.codex_context_window,
                "effective_context_window_percent": 95,
                "experimental_supported_tools": [],
                "input_modalities": ["text"],
                "supports_search_tool": False,
                "use_responses_lite": True,
            }
        ]
    }
    _write_json(path, catalog)


def _write_codex_acp_wrapper(path: Path, executable: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    script = (
        "#!/bin/sh\n"
        f"exec {shlex.quote(executable)} "
        "-c 'approval_policy=\"never\"' "
        "-c 'sandbox_mode=\"danger-full-access\"' "
        "-c 'shell_environment_policy.inherit=\"all\"' "
        "\"$@\"\n"
    )
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)


def _write_codex_config(path: Path, args: argparse.Namespace, model_catalog_path: Path) -> None:
    provider = args.codex_provider
    config = (
        f'model = "{args.codex_model}"\n'
        f'model_provider = "{provider}"\n'
        f'model_catalog_json = "{model_catalog_path}"\n'
        f"model_context_window = {args.codex_context_window}\n"
        f"model_auto_compact_token_limit = {args.codex_auto_compact_limit}\n"
        'model_reasoning_effort = "minimal"\n'
        'model_reasoning_summary = "none"\n'
        "model_supports_reasoning_summaries = false\n"
        'approval_policy = "never"\n'
        'sandbox_mode = "danger-full-access"\n'
        'model_verbosity = "low"\n'
        'web_search = "disabled"\n\n'
        "[shell_environment_policy]\n"
        'inherit = "all"\n'
        "ignore_default_excludes = false\n"
        'exclude = ["*PASSWORD*", "*TOKEN*", "*SECRET*", "*COOKIE*", "*SESSION*"]\n\n'
        "[features]\n"
        "multi_agent = false\n\n"
        f"[model_providers.{provider}]\n"
        'name = "North vLLM"\n'
        f'base_url = "{args.codex_base_url}"\n'
        'wire_api = "responses"\n'
    )
    path.write_text(config, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.mcp_port is None:
        args.mcp_port = _choose_mcp_port()
    root = _repo_root()

    env = os.environ.copy()
    if not env.get("PLATFORM_BACKEND_URL") and not env.get("MIP_BASE_URL"):
        env["PLATFORM_BACKEND_URL"] = DEFAULT_BACKEND_URL
    backend_url = env.get("PLATFORM_BACKEND_URL") or env.get("MIP_BASE_URL")
    url = f"http://{args.host}:{args.port}/lab/tree/{args.notebook}?token={args.token}"

    with tempfile.TemporaryDirectory(prefix="mip-codex-home-") as codex_home:
        codex_home_path = Path(codex_home)
        model_catalog_path = codex_home_path / "model-catalog.json"
        _write_codex_model_catalog(model_catalog_path, args)
        _write_codex_config(codex_home_path / "config.toml", args, model_catalog_path)

        native_mcp_forwarding = args.enable_native_jupyter_mcp and not args.disable_jupyter_mcp
        persona_manager_config = {"default_persona_id": DEFAULT_CODEX_PERSONA_ID}
        if not native_mcp_forwarding:
            persona_manager_config["builtin_mcp_servers"] = []
        jupyter_config = {
            "PersonaManager": persona_manager_config,
            "MCPExtensionApp": {
                "mcp_port": args.mcp_port,
                "use_tool_discovery": False,
                "mcp_tools": SAFE_JUPYTER_MCP_TOOLS,
            },
        }
        jupyter_config_path = codex_home_path / "jupyter_ai_config.json"
        _write_json(jupyter_config_path, jupyter_config)

        env["CODEX_HOME"] = codex_home
        codex_acp_wrapper = None
        codex_acp_path = shutil.which("codex-acp")
        if codex_acp_path:
            codex_acp_wrapper = codex_home_path / "bin" / "codex-acp"
            _write_codex_acp_wrapper(codex_acp_wrapper, codex_acp_path)
            env["PATH"] = f"{codex_acp_wrapper.parent}{os.pathsep}{env.get('PATH', '')}"
        env["JUPYTER_MCP_URL"] = f"http://127.0.0.1:{args.mcp_port}/mcp"

        command = [
            sys.executable,
            "-m",
            "jupyterlab",
            "--no-browser",
            f"--ServerApp.ip={args.host}",
            f"--ServerApp.port={args.port}",
            f"--ServerApp.token={args.token}",
            f"--ServerApp.root_dir={root}",
            f"--ServerApp.default_url=/lab/tree/{args.notebook}",
            "--config",
            str(jupyter_config_path),
        ]

        print(f"JupyterLab URL: {url}")
        print(f"PLATFORM_BACKEND_URL={backend_url}")
        print("Jupyter AI persona: Codex")
        print(f"CODEX_HOME={codex_home}")
        print(f"Codex model: {args.codex_model}")
        print(f"Codex provider: {args.codex_provider}")
        print(f"Codex base_url: {args.codex_base_url}")
        mcp_forwarding = "native" if native_mcp_forwarding else "shell bridge"
        print(f"Codex model catalog: {model_catalog_path}")
        if codex_acp_wrapper:
            print(f"Codex ACP wrapper: {codex_acp_wrapper}")
        print(f"Jupyter MCP forwarding: {mcp_forwarding}")
        print(f"Jupyter MCP port: {args.mcp_port}")
        print(f"Jupyter MCP URL: {env['JUPYTER_MCP_URL']}")
        print(f"Jupyter MCP tools: {len(SAFE_JUPYTER_MCP_TOOLS)} safe wrappers")
        return subprocess.call(command, cwd=root, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
