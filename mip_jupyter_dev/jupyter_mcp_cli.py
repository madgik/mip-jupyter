"""Command-line bridge for calling the local Jupyter MCP server."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import Request
from urllib.request import urlopen

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
    if getattr(args, "content_file", None):
        if args.content_file == "-":
            return sys.stdin.read()
        with open(args.content_file, encoding="utf-8") as handle:
            return handle.read()
    return " ".join(getattr(args, "content", []) or [])


def _text_arg(value: list[str] | str | None) -> str:
    if isinstance(value, list):
        return " ".join(value)
    return str(value or "")


def _add_content_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("content", nargs="*")
    parser.add_argument("--content-file")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Call the local curated Jupyter MCP server.")
    parser.add_argument("--mcp-url", default=os.getenv("JUPYTER_MCP_URL", DEFAULT_MCP_URL))
    subparsers = parser.add_subparsers(dest="command", required=True)

    read_guide = subparsers.add_parser("read-guide", help="Read the production agent guide")
    read_guide.add_argument("--topic")

    search_docs = subparsers.add_parser("search-docs", help="Search workspace docs")
    search_docs.add_argument("query", nargs="+")
    search_docs.add_argument("--limit", type=int, default=5)

    outline = subparsers.add_parser("notebook-outline", help="Summarize notebook cells without full outputs")
    outline.add_argument("path")

    read_cell = subparsers.add_parser("read-cell", help="Read one notebook cell")
    read_cell.add_argument("path")
    read_cell.add_argument("index", type=int)
    read_cell.add_argument("--max-chars", type=int, default=4000)

    create = subparsers.add_parser("create-notebook", help="Create a notebook")
    create.add_argument("path")
    create.add_argument("--kernel-name", default="python3")

    append_md = subparsers.add_parser("append-markdown", help="Append a markdown cell")
    append_md.add_argument("path")
    _add_content_args(append_md)

    append_code = subparsers.add_parser("append-code", help="Append a code cell")
    append_code.add_argument("path")
    _add_content_args(append_code)

    edit = subparsers.add_parser("edit-cell", help="Replace a notebook cell by index")
    edit.add_argument("path")
    edit.add_argument("index", type=int)
    _add_content_args(edit)
    edit.add_argument("--cell-type", default="code", choices=["code", "markdown", "raw"])

    run_cell = subparsers.add_parser("run-cell", help="Run one notebook cell")
    run_cell.add_argument("path")
    run_cell.add_argument("index", type=int)
    run_cell.add_argument("--timeout", type=float, default=30.0)

    run_all = subparsers.add_parser("run-all-cells", help="Run all cells in a notebook")
    run_all.add_argument("path")
    run_all.add_argument("--timeout", type=float, default=30.0)

    open_file = subparsers.add_parser("open-file", help="Open a file in JupyterLab")
    open_file.add_argument("path")

    env_status = subparsers.add_parser("mip-env-status", help="Report MIP env var presence without secrets")
    env_status.set_defaults(no_args=True)

    catalog = subparsers.add_parser("mip-catalog-summary", help="List compact data-model summaries")
    catalog.add_argument("--limit", type=int, default=20)

    data_model = subparsers.add_parser("mip-data-model-summary", help="Summarize one data model")
    data_model.add_argument("code")
    data_model.add_argument("--version")
    data_model.add_argument("--include-variables", action="store_true")

    search_vars = subparsers.add_parser("mip-search-variables", help="Search variables in a data model")
    search_vars.add_argument("code")
    search_vars.add_argument("query", nargs="+")
    search_vars.add_argument("--version")
    search_vars.add_argument("--limit", type=int, default=20)

    algorithms = subparsers.add_parser("mip-algorithm-summary", help="List compact algorithm summaries")
    algorithms.set_defaults(no_args=True)

    legacy_md = subparsers.add_parser("add-markdown", help="Alias for append-markdown")
    legacy_md.add_argument("path")
    _add_content_args(legacy_md)

    legacy_code = subparsers.add_parser("add-code", help="Alias for append-code")
    legacy_code.add_argument("path")
    _add_content_args(legacy_code)

    legacy_read = subparsers.add_parser("read-notebook", help="Alias for notebook-outline")
    legacy_read.add_argument("path")

    return parser


def _tool_call_for_args(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    command = args.command
    if command == "read-guide":
        return "agent_read_guide", {"topic": args.topic}
    if command == "search-docs":
        return "agent_search_docs", {"query": _text_arg(args.query), "limit": args.limit}
    if command in {"notebook-outline", "read-notebook"}:
        return "notebook_outline", {"path": args.path}
    if command == "read-cell":
        return "notebook_read_cell", {"path": args.path, "index": args.index, "max_chars": args.max_chars}
    if command == "create-notebook":
        return "create_notebook", {"path": args.path, "kernel_name": args.kernel_name}
    if command in {"append-markdown", "add-markdown"}:
        return "append_markdown_cell", {"path": args.path, "content": _content_from_args(args)}
    if command in {"append-code", "add-code"}:
        return "append_code_cell", {"path": args.path, "content": _content_from_args(args)}
    if command == "edit-cell":
        return (
            "edit_cell_by_index",
            {"path": args.path, "index": args.index, "content": _content_from_args(args), "cell_type": args.cell_type},
        )
    if command == "run-cell":
        return "run_cell_by_index", {"path": args.path, "index": args.index, "timeout": args.timeout}
    if command == "run-all-cells":
        return "run_all_cells", {"path": args.path, "timeout": args.timeout}
    if command == "open-file":
        return "open_file", {"path": args.path}
    if command == "mip-env-status":
        return "mip_env_status", {}
    if command == "mip-catalog-summary":
        return "mip_catalog_summary", {"limit": args.limit}
    if command == "mip-data-model-summary":
        return (
            "mip_data_model_summary",
            {"code": args.code, "version": args.version, "include_variables": args.include_variables},
        )
    if command == "mip-search-variables":
        return (
            "mip_search_variables",
            {"code": args.code, "version": args.version, "query": _text_arg(args.query), "limit": args.limit},
        )
    if command == "mip-algorithm-summary":
        return "mip_algorithm_summary", {}
    raise AssertionError(command)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    name, arguments = _tool_call_for_args(args)
    result = call_tool(args.mcp_url, name, arguments)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
