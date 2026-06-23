"""Command-line bridge for calling the local Jupyter MCP server."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_MCP_URL = "http://127.0.0.1:3001/mcp"


def _parse_sse_response(body: bytes) -> dict[str, Any]:
    if not body.strip():
        return {}
    data_lines: list[str] = []
    for raw_line in body.decode("utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("data:"):
            data_lines.append(line[5:].strip())
    if not data_lines:
        return json.loads(body.decode("utf-8"))
    return json.loads("\n".join(data_lines))


def _post_json(url: str, payload: dict[str, Any], session_id: str | None = None) -> tuple[dict[str, Any], str | None]:
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    if session_id:
        headers["mcp-session-id"] = session_id
    request = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urlopen(request, timeout=30) as response:
            parsed = _parse_sse_response(response.read())
            return parsed, response.headers.get("mcp-session-id") or session_id
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"MCP HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not connect to Jupyter MCP server at {url}: {exc.reason}") from exc


def _initialize(url: str) -> str:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mip-jupyter-mcp-cli", "version": "0"},
        },
    }
    response, session_id = _post_json(url, payload)
    if "error" in response:
        raise RuntimeError(json.dumps(response["error"], indent=2))
    if not session_id:
        raise RuntimeError("Jupyter MCP server did not return an MCP session id")
    _post_json(
        url,
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        session_id=session_id,
    )
    return session_id


def call_tool(url: str, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    session_id = _initialize(url)
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    response, _session_id = _post_json(url, payload, session_id=session_id)
    if "error" in response:
        raise RuntimeError(json.dumps(response["error"], indent=2))
    return response.get("result", response)


def _content_from_args(args: argparse.Namespace) -> str:
    if args.content_file:
        if args.content_file == "-":
            return sys.stdin.read()
        with open(args.content_file, encoding="utf-8") as handle:
            return handle.read()
    return " ".join(args.content or [])


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Call the local Jupyter MCP server.")
    parser.add_argument("--mcp-url", default=os.getenv("JUPYTER_MCP_URL", DEFAULT_MCP_URL))
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create-notebook", help="Create a notebook")
    create.add_argument("file_path")
    create.add_argument("--kernel-name", default="python3")

    add_md = subparsers.add_parser("add-markdown", help="Append a markdown cell")
    add_md.add_argument("file_path")
    add_md.add_argument("content", nargs="*")
    add_md.add_argument("--content-file")

    add_code = subparsers.add_parser("add-code", help="Append a code cell")
    add_code.add_argument("file_path")
    add_code.add_argument("content", nargs="*")
    add_code.add_argument("--content-file")

    edit = subparsers.add_parser("edit-cell", help="Replace a notebook cell by index")
    edit.add_argument("file_path")
    edit.add_argument("cell_index", type=int)
    edit.add_argument("content", nargs="*")
    edit.add_argument("--cell-type", default="code", choices=["code", "markdown", "raw"])
    edit.add_argument("--content-file")

    read = subparsers.add_parser("read-notebook", help="Read notebook cells")
    read.add_argument("file_path")

    open_file = subparsers.add_parser("open-file", help="Open a file in JupyterLab")
    open_file.add_argument("file_path")

    run_all = subparsers.add_parser("run-all-cells", help="Run all cells in the active notebook")
    run_all.add_argument("--timeout", type=float, default=10.0)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "create-notebook":
        result = call_tool(args.mcp_url, "create_notebook", {"file_path": args.file_path, "kernel_name": args.kernel_name})
    elif args.command == "add-markdown":
        result = call_tool(args.mcp_url, "add_markdown_cell", {"file_path": args.file_path, "content": _content_from_args(args)})
    elif args.command == "add-code":
        result = call_tool(args.mcp_url, "add_code_cell", {"file_path": args.file_path, "content": _content_from_args(args)})
    elif args.command == "edit-cell":
        result = call_tool(
            args.mcp_url,
            "edit_cell_by_index",
            {
                "file_path": args.file_path,
                "cell_index": args.cell_index,
                "content": _content_from_args(args),
                "cell_type": args.cell_type,
            },
        )
    elif args.command == "read-notebook":
        result = call_tool(args.mcp_url, "read_notebook_cells", {"file_path": args.file_path})
    elif args.command == "open-file":
        result = call_tool(args.mcp_url, "open_file", {"file_path": args.file_path})
    elif args.command == "run-all-cells":
        result = call_tool(args.mcp_url, "run_all_cells", {"timeout": args.timeout})
    else:
        raise AssertionError(args.command)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
