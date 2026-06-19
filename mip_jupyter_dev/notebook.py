"""Start the local classic Notebook server for mip-jupyter."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


DEFAULT_BACKEND_URL = "http://127.0.0.1:8080/services"
DEFAULT_TOKEN = "dev"
DEFAULT_NOTEBOOK = "feres_analysis.ipynb"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8888


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Start local Jupyter Notebook for mip-jupyter.")
    parser.add_argument("--notebook", default=os.getenv("MIP_NOTEBOOK", DEFAULT_NOTEBOOK))
    parser.add_argument("--host", default=os.getenv("JUPYTER_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.getenv("JUPYTER_PORT", str(DEFAULT_PORT))))
    parser.add_argument("--token", default=os.getenv("JUPYTER_TOKEN", DEFAULT_TOKEN))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = _repo_root()

    env = os.environ.copy()
    if not env.get("PLATFORM_BACKEND_URL") and not env.get("MIP_BASE_URL"):
        env["PLATFORM_BACKEND_URL"] = DEFAULT_BACKEND_URL

    command = [
        sys.executable,
        "-m",
        "notebook",
        "--no-browser",
        f"--ip={args.host}",
        f"--port={args.port}",
        f"--ServerApp.token={args.token}",
        f"--ServerApp.root_dir={root}",
        f"--ServerApp.default_url=/tree/{args.notebook}",
    ]
    print(f"Notebook URL: http://{args.host}:{args.port}/tree/{args.notebook}?token={args.token}")
    backend_url = env.get("PLATFORM_BACKEND_URL") or env.get("MIP_BASE_URL")
    print(f"PLATFORM_BACKEND_URL={backend_url}")
    return subprocess.call(command, cwd=root, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
