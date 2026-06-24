"""Curated, production-safe Jupyter MCP tools for mip-jupyter."""

from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any
from typing import Literal


GUIDE_RELATIVE_PATH = Path("llm") / "wiki" / "00-agent-workspace.md"
BLOCKED_PATH_PARTS = {".ipynb_checkpoints", ".venv", ".playwright-cli", "__pycache__"}
MAX_DOC_RESULTS = 10
MAX_DOC_SNIPPET_CHARS = 600
MAX_CELL_READ_CHARS = 20000
MAX_LIST_ITEMS = 100
SAFE_JUPYTER_MCP_TOOLS = [
    "mip_jupyter_dev.jupyter_mcp_tools:agent_read_guide",
    "mip_jupyter_dev.jupyter_mcp_tools:agent_search_docs",
    "mip_jupyter_dev.jupyter_mcp_tools:notebook_outline",
    "mip_jupyter_dev.jupyter_mcp_tools:notebook_read_cell",
    "mip_jupyter_dev.jupyter_mcp_tools:create_notebook",
    "mip_jupyter_dev.jupyter_mcp_tools:append_markdown_cell",
    "mip_jupyter_dev.jupyter_mcp_tools:append_code_cell",
    "mip_jupyter_dev.jupyter_mcp_tools:edit_cell_by_index",
    "mip_jupyter_dev.jupyter_mcp_tools:run_cell_by_index",
    "mip_jupyter_dev.jupyter_mcp_tools:run_all_cells",
    "mip_jupyter_dev.jupyter_mcp_tools:open_file",
    "mip_jupyter_dev.jupyter_mcp_tools:mip_env_status",
    "mip_jupyter_dev.jupyter_mcp_tools:mip_catalog_summary",
    "mip_jupyter_dev.jupyter_mcp_tools:mip_data_model_summary",
    "mip_jupyter_dev.jupyter_mcp_tools:mip_search_variables",
    "mip_jupyter_dev.jupyter_mcp_tools:mip_algorithm_summary",
]


def _workspace_root() -> Path:
    configured = os.getenv("MIP_JUPYTER_ROOT")
    if configured:
        path = Path(configured).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        return path.resolve()

    cwd = Path.cwd().resolve()
    local_workspace = cwd / "workspace"
    if local_workspace.is_dir():
        return local_workspace.resolve()
    return cwd


def _strip_workspace_prefix(path: str) -> str:
    parsed = PurePosixPath(path.replace("\\", "/"))
    if parsed.is_absolute():
        return path
    parts = parsed.parts
    if parts and parts[0] == "workspace":
        return PurePosixPath(*parts[1:]).as_posix()
    return parsed.as_posix()


def _require_within_workspace(path: Path) -> None:
    root = _workspace_root()
    try:
        path.resolve().relative_to(root)
    except ValueError as exc:
        raise ValueError("Path must stay under the Jupyter workspace.") from exc


def _workspace_relative_path(path: str) -> Path:
    raw = str(path or "").strip()
    if not raw:
        raise ValueError("Path is required.")

    normalized = _strip_workspace_prefix(raw)
    parsed = PurePosixPath(normalized.replace("\\", "/"))
    if parsed.is_absolute():
        candidate = Path(normalized).expanduser().resolve()
        _require_within_workspace(candidate)
        relative = candidate.relative_to(_workspace_root())
    else:
        if any(part == ".." for part in parsed.parts):
            raise ValueError("Path must not contain '..'.")
        if any(part in BLOCKED_PATH_PARTS for part in parsed.parts):
            raise ValueError("Path points to a blocked workspace location.")
        relative = Path(*parsed.parts)
        candidate = (_workspace_root() / relative).resolve()
        _require_within_workspace(candidate)
    return relative


def _workspace_file(path: str) -> tuple[Path, Path]:
    relative = _workspace_relative_path(path)
    return relative, _workspace_root() / relative


def _server_path(relative_path: Path) -> str:
    """Return the Jupyter-server-visible path for local dev or production roots."""

    root = _workspace_root()
    cwd = Path.cwd().resolve()
    try:
        root_prefix = root.relative_to(cwd)
    except ValueError:
        root_prefix = Path()
    if str(root_prefix) in {"", "."}:
        return relative_path.as_posix()
    return (root_prefix / relative_path).as_posix()


def _limit(value: int | str | None, default: int, maximum: int) -> int:
    if value is None:
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(parsed, maximum))


def _truncate(text: Any, max_chars: int, *, suffix: str = "...") -> str:
    value = str(text or "")
    if len(value) <= max_chars:
        return value
    if max_chars <= len(suffix):
        return value[:max_chars]
    return value[: max_chars - len(suffix)] + suffix


def _cell_source(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(str(item) for item in source)
    return str(source or "")


def _source_preview(source: str, max_chars: int = 240) -> str:
    lines = [line.rstrip() for line in source.strip().splitlines()]
    preview = "\n".join(lines[:8])
    return _truncate(preview, max_chars)


def _markdown_headings(source: str) -> list[str]:
    headings: list[str] = []
    for line in source.splitlines():
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", line)
        if match:
            headings.append(match.group(1).strip())
        if len(headings) >= 5:
            break
    return headings


def _output_summary(outputs: list[dict[str, Any]], *, max_outputs: int = 5) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for output in outputs[:max_outputs]:
        output_type = output.get("output_type")
        item: dict[str, Any] = {"output_type": output_type}
        if output_type == "error":
            item["ename"] = output.get("ename")
            item["evalue"] = _truncate(output.get("evalue"), 240)
        elif "text" in output:
            item["text_preview"] = _truncate(_join_maybe_list(output.get("text")), 240)
        elif isinstance(output.get("data"), dict):
            data = output["data"]
            item["data_keys"] = sorted(str(key) for key in data.keys())
            if "text/plain" in data:
                item["text_preview"] = _truncate(_join_maybe_list(data["text/plain"]), 240)
        summaries.append(item)
    if len(outputs) > max_outputs:
        summaries.append({"truncated_outputs": len(outputs) - max_outputs})
    return summaries


def _join_maybe_list(value: Any) -> str:
    if isinstance(value, list):
        return "".join(str(item) for item in value)
    return str(value or "")


def _outline_cell(index: int, cell: dict[str, Any]) -> dict[str, Any]:
    source = _cell_source(cell)
    outputs = cell.get("outputs") or []
    if not isinstance(outputs, list):
        outputs = []
    cell_type = cell.get("cell_type")
    outline = {
        "index": index,
        "cell_type": cell_type,
        "source_preview": _source_preview(source),
        "source_chars": len(source),
        "output_count": len(outputs),
        "error_count": sum(1 for output in outputs if output.get("output_type") == "error"),
    }
    if cell_type == "markdown":
        outline["headings"] = _markdown_headings(source)
    if cell_type == "code":
        outline["execution_count"] = cell.get("execution_count")
    return outline


def _read_notebook_data(path: str) -> tuple[Path, Path, dict[str, Any]]:
    relative, file_path = _workspace_file(path)
    if file_path.suffix != ".ipynb":
        raise ValueError("Notebook path must end with .ipynb.")
    with file_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("cells"), list):
        raise ValueError("File is not a valid notebook.")
    return relative, file_path, data


def _write_notebook_data(file_path: Path, data: dict[str, Any]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def _new_notebook(kernel_name: str) -> dict[str, Any]:
    return {
        "cells": [],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3" if kernel_name == "python3" else kernel_name,
                "language": "python",
                "name": kernel_name,
            },
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def _new_cell(content: str, cell_type: Literal["code", "markdown", "raw"]) -> dict[str, Any]:
    cell = {"cell_type": cell_type, "metadata": {}, "source": str(content or "")}
    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    return cell


def _agent_docs_root() -> Path | None:
    configured = os.getenv("MIP_AGENT_DOCS")
    if configured:
        path = Path(configured).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        resolved = path.resolve()
        if resolved.is_dir():
            return resolved
    repo = Path(__file__).resolve().parents[1]
    if (repo / "docs" / "llm").is_dir():
        return repo
    return None


def _agent_guide_path() -> Path | None:
    candidates: list[Path] = []
    agent_root = _agent_docs_root()
    if agent_root is not None:
        candidates.append(agent_root / GUIDE_RELATIVE_PATH)
        candidates.append(agent_root / "docs" / GUIDE_RELATIVE_PATH)
    for path in candidates:
        if path.is_file():
            return path
    return None


def _doc_files() -> list[Path]:
    docs_root = _workspace_root() / "docs"
    if not docs_root.is_dir():
        return []
    files = []
    for path in sorted(docs_root.rglob("*.md")):
        if any(part in BLOCKED_PATH_PARTS for part in path.parts):
            continue
        try:
            path.relative_to(docs_root)
        except ValueError:
            continue
        files.append(path)
    return files


def _workspace_display_path(path: Path) -> str:
    return path.relative_to(_workspace_root()).as_posix()


def _markdown_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def _snippet_for_query(text: str, query: str) -> str:
    lower_text = text.lower()
    terms = [term for term in re.split(r"\W+", query.lower()) if term]
    positions = [lower_text.find(term) for term in terms if lower_text.find(term) >= 0]
    start = max(0, min(positions) - 120) if positions else 0
    snippet = text[start : start + MAX_DOC_SNIPPET_CHARS].strip()
    return _truncate(snippet.replace("\r\n", "\n"), MAX_DOC_SNIPPET_CHARS)


def _section_matches(text: str, topic: str) -> list[str]:
    terms = [term for term in re.split(r"\W+", topic.lower()) if term]
    if not terms:
        return [text]
    sections: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("#") and current:
            section = "\n".join(current).strip()
            lower = section.lower()
            if any(term in lower for term in terms):
                sections.append(section)
            current = [line]
        else:
            current.append(line)
    if current:
        section = "\n".join(current).strip()
        lower = section.lower()
        if any(term in lower for term in terms):
            sections.append(section)
    return sections


async def agent_read_guide(topic: str | None = None) -> dict[str, Any]:
    """Read the agent workspace guide, optionally narrowed by topic."""

    guide_path = _agent_guide_path()
    if guide_path is None:
        return {
            "ok": False,
            "path": GUIDE_RELATIVE_PATH.as_posix(),
            "error": "Agent workspace guide is missing.",
        }
    text = guide_path.read_text(encoding="utf-8")
    if topic:
        matches = _section_matches(text, topic)
        content = "\n\n".join(matches) if matches else ""
    else:
        content = text
    display_path = GUIDE_RELATIVE_PATH.as_posix()
    return {
        "ok": True,
        "path": display_path,
        "topic": topic,
        "content": _truncate(content, 8000),
        "truncated": len(content) > 8000,
    }


async def agent_search_docs(query: str, limit: int = 5) -> dict[str, Any]:
    """Search workspace docs and return bounded snippets."""

    query = str(query or "").strip()
    if not query:
        raise ValueError("query is required.")
    limit = _limit(limit, 5, MAX_DOC_RESULTS)
    terms = [term for term in re.split(r"\W+", query.lower()) if term]
    results: list[dict[str, Any]] = []
    for path in _doc_files():
        text = path.read_text(encoding="utf-8")
        haystack = text.lower()
        score = sum(haystack.count(term) for term in terms)
        if score <= 0:
            continue
        results.append(
            {
                "path": _workspace_display_path(path),
                "title": _markdown_title(text, path.name),
                "score": score,
                "snippet": _snippet_for_query(text, query),
            }
        )
    results.sort(key=lambda item: (-int(item["score"]), str(item["path"])))
    return {"ok": True, "query": query, "count": len(results), "results": results[:limit]}


async def notebook_outline(path: str) -> dict[str, Any]:
    """Return a bounded notebook outline without full outputs."""

    relative, _file_path, data = _read_notebook_data(path)
    cells = data.get("cells") or []
    return {
        "ok": True,
        "path": relative.as_posix(),
        "cell_count": len(cells),
        "cells": [_outline_cell(index, cell) for index, cell in enumerate(cells)],
    }


async def notebook_read_cell(path: str, index: int, max_chars: int = 4000) -> dict[str, Any]:
    """Read one notebook cell source with bounded output summaries."""

    max_chars = _limit(max_chars, 4000, MAX_CELL_READ_CHARS)
    relative, _file_path, data = _read_notebook_data(path)
    cells = data.get("cells") or []
    if index < 0 or index >= len(cells):
        raise IndexError(f"Cell index {index} is out of range for {len(cells)} cells.")
    cell = cells[index]
    source = _cell_source(cell)
    outputs = cell.get("outputs") or []
    if not isinstance(outputs, list):
        outputs = []
    return {
        "ok": True,
        "path": relative.as_posix(),
        "index": index,
        "cell_type": cell.get("cell_type"),
        "source": source[:max_chars],
        "source_chars": len(source),
        "source_truncated": len(source) > max_chars,
        "output_count": len(outputs),
        "error_count": sum(1 for output in outputs if output.get("output_type") == "error"),
        "outputs": _output_summary(outputs),
    }


async def create_notebook(path: str, kernel_name: str = "python3") -> dict[str, Any]:
    """Create an empty notebook under the workspace."""

    relative, file_path = _workspace_file(path)
    if file_path.suffix != ".ipynb":
        raise ValueError("Notebook path must end with .ipynb.")
    if file_path.exists():
        raise FileExistsError(f"Notebook already exists: {relative.as_posix()}")
    data = _new_notebook(kernel_name)
    _write_notebook_data(file_path, data)
    return {"ok": True, "path": relative.as_posix(), "jupyter_path": _server_path(relative)}


async def append_markdown_cell(path: str, content: str) -> dict[str, Any]:
    """Append a markdown cell to a notebook."""

    relative, file_path, data = _read_notebook_data(path)
    data["cells"].append(_new_cell(content, "markdown"))
    _write_notebook_data(file_path, data)
    return {"ok": True, "path": relative.as_posix(), "index": len(data["cells"]) - 1}


async def append_code_cell(path: str, content: str) -> dict[str, Any]:
    """Append a code cell to a notebook."""

    relative, file_path, data = _read_notebook_data(path)
    data["cells"].append(_new_cell(content, "code"))
    _write_notebook_data(file_path, data)
    return {"ok": True, "path": relative.as_posix(), "index": len(data["cells"]) - 1}


async def edit_cell_by_index(
    path: str,
    index: int,
    content: str,
    cell_type: Literal["code", "markdown", "raw"] = "code",
) -> dict[str, Any]:
    """Replace a notebook cell by numeric index."""

    relative, file_path, data = _read_notebook_data(path)
    cells = data.get("cells") or []
    if index < 0 or index >= len(cells):
        raise IndexError(f"Cell index {index} is out of range for {len(cells)} cells.")
    data["cells"][index] = _new_cell(content, cell_type)
    _write_notebook_data(file_path, data)
    return {"ok": True, "path": relative.as_posix(), "index": index, "cell_type": cell_type}


def _execute_notebook(path: Path, data: dict[str, Any], *, timeout: float, index: int | None) -> dict[str, Any]:
    try:
        import nbformat
        from nbclient import NotebookClient
    except ImportError as exc:
        raise RuntimeError("Notebook execution requires nbformat and nbclient.") from exc

    notebook_node = nbformat.from_dict(deepcopy(data))
    cells = notebook_node.cells
    if index is not None:
        if index < 0 or index >= len(cells):
            raise IndexError(f"Cell index {index} is out of range for {len(cells)} cells.")
        selected = deepcopy(notebook_node)
        selected.cells = [deepcopy(cells[index])]
        NotebookClient(selected, timeout=timeout, allow_errors=True).execute()
        notebook_node.cells[index] = selected.cells[0]
        executed_indexes = [index]
    else:
        NotebookClient(notebook_node, timeout=timeout, allow_errors=True).execute()
        executed_indexes = list(range(len(cells)))

    nbformat.write(notebook_node, path)
    executed_cells = [
        _outline_cell(cell_index, json.loads(json.dumps(notebook_node.cells[cell_index])))
        for cell_index in executed_indexes
    ]
    total_errors = sum(int(cell["error_count"]) for cell in executed_cells)
    return {"ok": total_errors == 0, "executed_cells": executed_cells, "error_count": total_errors}


async def run_cell_by_index(path: str, index: int, timeout: float = 30.0) -> dict[str, Any]:
    """Execute one notebook cell in an isolated kernel and write its outputs."""

    relative, file_path, data = _read_notebook_data(path)
    result = _execute_notebook(file_path, data, timeout=float(timeout), index=index)
    result["path"] = relative.as_posix()
    return result


async def run_all_cells(path: str, timeout: float = 30.0) -> dict[str, Any]:
    """Execute all cells in a notebook and write bounded execution summaries."""

    relative, file_path, data = _read_notebook_data(path)
    result = _execute_notebook(file_path, data, timeout=float(timeout), index=None)
    result["path"] = relative.as_posix()
    return result


async def open_file(path: str) -> dict[str, Any]:
    """Open a workspace file in the JupyterLab main area."""

    relative = _workspace_relative_path(path)
    try:
        from jupyter_ai_tools.toolkits import jupyterlab
    except ImportError as exc:
        raise RuntimeError("open_file requires Jupyter AI tools in a running JupyterLab server.") from exc
    return await jupyterlab.open_file(file_path=_server_path(relative))


async def mip_env_status() -> dict[str, Any]:
    """Report MIP backend configuration presence without exposing secrets."""

    backend_source = None
    for name in ("PLATFORM_BACKEND_URL", "MIP_BASE_URL"):
        if os.getenv(name):
            backend_source = name
            break

    token_source = None
    for name in ("PLATFORM_TOKEN", "MIP_TOKEN"):
        if os.getenv(name):
            token_source = name
            break
    if token_source is None:
        for token_file in (_workspace_root() / "mip_token", _workspace_root() / ".mip_token"):
            if token_file.is_file() and token_file.stat().st_size > 0:
                token_source = token_file.name
                break

    return {
        "ok": True,
        "backend_url_present": backend_source is not None,
        "backend_url_source": backend_source,
        "token_present": token_source is not None,
        "token_source": token_source,
        "timeout_present": os.getenv("PLATFORM_BACKEND_TIMEOUT") is not None,
    }


def _mip_client():
    from mip import Client

    return Client.from_env()


def _tool_error(exc: Exception) -> dict[str, Any]:
    return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}


async def mip_catalog_summary(limit: int = 20) -> dict[str, Any]:
    """Return compact authorized data-model summaries from platform-backend."""

    limit = _limit(limit, 20, MAX_LIST_ITEMS)
    try:
        summaries = _mip_client().catalog().summaries()
    except Exception as exc:  # noqa: BLE001 - MCP tools should return structured errors.
        return _tool_error(exc)
    return {
        "ok": True,
        "count": len(summaries),
        "items": summaries[:limit],
        "truncated": len(summaries) > limit,
    }


async def mip_data_model_summary(
    code: str,
    version: str | None = None,
    include_variables: bool = False,
) -> dict[str, Any]:
    """Return compact metadata for one data model."""

    try:
        data_model = _mip_client().catalog().data_model(code, version=version)
        variables = data_model.list_variables() if include_variables else []
        groups = data_model.list_groups()
        datasets = data_model.list_datasets()
    except Exception as exc:  # noqa: BLE001 - MCP tools should return structured errors.
        return _tool_error(exc)

    return {
        "ok": True,
        "summary": data_model.summary(),
        "datasets": datasets[:MAX_LIST_ITEMS],
        "datasets_truncated": len(datasets) > MAX_LIST_ITEMS,
        "groups": groups[:MAX_LIST_ITEMS],
        "groups_truncated": len(groups) > MAX_LIST_ITEMS,
        "variables": variables[:MAX_LIST_ITEMS],
        "variables_truncated": len(variables) > MAX_LIST_ITEMS,
    }


async def mip_search_variables(
    code: str,
    query: str,
    version: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Search variables in one data model by code or label."""

    limit = _limit(limit, 20, MAX_LIST_ITEMS)
    try:
        data_model = _mip_client().catalog().data_model(code, version=version)
        matches = [variable.summary() for variable in data_model.variables.search(query)]
    except Exception as exc:  # noqa: BLE001 - MCP tools should return structured errors.
        return _tool_error(exc)
    return {
        "ok": True,
        "code": code,
        "version": version,
        "query": query,
        "count": len(matches),
        "items": matches[:limit],
        "truncated": len(matches) > limit,
    }


async def mip_algorithm_summary() -> dict[str, Any]:
    """Return compact algorithm summaries from platform-backend."""

    try:
        algorithms = _mip_client().algorithms().list()
        summaries = [algorithm.summary() for algorithm in algorithms]
    except Exception as exc:  # noqa: BLE001 - MCP tools should return structured errors.
        return _tool_error(exc)

    counts_by_type: dict[str, int] = {}
    for item in summaries:
        kind = str(item.get("type") or "unknown")
        counts_by_type[kind] = counts_by_type.get(kind, 0) + 1
    return {
        "ok": True,
        "count": len(summaries),
        "counts_by_type": counts_by_type,
        "items": summaries[:MAX_LIST_ITEMS],
        "truncated": len(summaries) > MAX_LIST_ITEMS,
    }
