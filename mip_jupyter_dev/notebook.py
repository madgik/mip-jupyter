"""Start local JupyterLab with Codex configured for mip-jupyter."""

from __future__ import annotations

import argparse
import errno
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

from .codex_bootstrap import (
    DEFAULT_CODEX_BASE_URL,
    DEFAULT_CODEX_MODEL,
    DEFAULT_CODEX_PROVIDER,
    DEFAULT_CODEX_CONTEXT_WINDOW,
    DEFAULT_CODEX_AUTO_COMPACT_LIMIT,
    DEFAULT_MCP_PORT,
    CodexSettings,
    bootstrap_codex,
)


DEFAULT_BACKEND_URL = "http://127.0.0.1:8080/services"
DEFAULT_TOKEN = "dev"
DEFAULT_NOTEBOOK = "workspace/examples/feres_analysis.ipynb"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8888


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


def _sync_workspace_user_docs(repo: Path) -> None:
    """Mirror docs/user into workspace/docs for local Jupyter parity with production."""
    src = repo / "docs" / "user"
    dest = repo / "workspace" / "docs"
    if not src.is_dir():
        return
    if dest.is_symlink():
        dest.unlink()
    elif dest.is_dir():
        shutil.rmtree(dest)
    try:
        dest.symlink_to(src.resolve(), target_is_directory=True)
    except OSError:
        shutil.copytree(src, dest)


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


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.mcp_port is None:
        args.mcp_port = _choose_mcp_port()
    root = _repo_root()
    _sync_workspace_user_docs(root)

    env = os.environ.copy()
    env.setdefault("MIP_JUPYTER_ROOT", str(root / "workspace"))
    if not env.get("MIP_AGENT_DOCS"):
        env["MIP_AGENT_DOCS"] = str(root)
    if not env.get("PLATFORM_BACKEND_URL") and not env.get("MIP_BASE_URL"):
        env["PLATFORM_BACKEND_URL"] = DEFAULT_BACKEND_URL
    backend_url = env.get("PLATFORM_BACKEND_URL") or env.get("MIP_BASE_URL")
    url = f"http://{args.host}:{args.port}/lab/tree/{args.notebook}?token={args.token}"

    native_mcp_forwarding = args.enable_native_jupyter_mcp and not args.disable_jupyter_mcp
    settings = CodexSettings(
        base_url=args.codex_base_url,
        model=args.codex_model,
        provider=args.codex_provider,
        context_window=args.codex_context_window,
        auto_compact_limit=args.codex_auto_compact_limit,
        mcp_port=args.mcp_port,
        enable_native_jupyter_mcp=native_mcp_forwarding,
    )

    with tempfile.TemporaryDirectory(prefix="mip-codex-home-") as codex_home:
        codex_home_path = Path(codex_home)
        jupyter_config_path = codex_home_path / "jupyter_ai_config.json"
        wrapper_bin = bootstrap_codex(codex_home_path, jupyter_config_path, settings)

        env["CODEX_HOME"] = codex_home
        if wrapper_bin is not None:
            env["PATH"] = f"{wrapper_bin}{os.pathsep}{env.get('PATH', '')}"
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
        print(f"Codex model: {settings.model}")
        print(f"Codex provider: {settings.provider}")
        print(f"Codex base_url: {settings.base_url}")
        mcp_forwarding = "native" if native_mcp_forwarding else "shell bridge"
        print(f"Codex model catalog: {codex_home_path / 'model-catalog.json'}")
        if wrapper_bin is not None:
            print(f"Codex ACP wrapper: {wrapper_bin / 'codex-acp'}")
        print(f"Jupyter MCP forwarding: {mcp_forwarding}")
        print(f"Jupyter MCP port: {args.mcp_port}")
        print(f"Jupyter MCP URL: {env['JUPYTER_MCP_URL']}")
        return subprocess.call(command, cwd=root, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
