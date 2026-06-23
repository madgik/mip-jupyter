"""Small, vLLM-compatible Jupyter MCP tool wrappers for mip-jupyter."""

from __future__ import annotations

from typing import Literal

from jupyter_ai_tools.toolkits import jupyterlab, notebook


async def create_notebook(file_path: str, kernel_name: str = "python3") -> str:
    """Create and open a notebook at file_path."""
    return await notebook.create_notebook(file_path=file_path, kernel_name=kernel_name)


async def add_markdown_cell(file_path: str, content: str) -> dict:
    """Append a markdown cell to a notebook."""
    await notebook.add_cell(file_path=file_path, content=content, cell_type="markdown")
    return {"success": True}


async def add_code_cell(file_path: str, content: str) -> dict:
    """Append a code cell to a notebook."""
    await notebook.add_cell(file_path=file_path, content=content, cell_type="code")
    return {"success": True}


async def edit_cell_by_index(
    file_path: str,
    cell_index: int,
    content: str,
    cell_type: Literal["code", "markdown", "raw"] = "code",
) -> dict:
    """Replace a notebook cell by numeric index."""
    cell_id = await notebook.get_cell_id_from_index(file_path=file_path, cell_index=cell_index)
    return await notebook.edit_cell(
        file_path=file_path,
        cell_id=cell_id,
        content=content,
        cell_type=cell_type,
    )


async def read_notebook_cells(file_path: str) -> list[dict]:
    """Read notebook cells as formatted dictionaries without outputs."""
    return await notebook.read_notebook_cells(notebook_path=file_path)


async def open_file(file_path: str) -> dict:
    """Open a file in the JupyterLab main area."""
    return await jupyterlab.open_file(file_path=file_path)


async def run_all_cells(timeout: float = 10.0) -> dict:
    """Run all cells in the active notebook."""
    return await jupyterlab.run_all_cells(timeout=timeout)
