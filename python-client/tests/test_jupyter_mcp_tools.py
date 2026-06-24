import asyncio
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / "python-client"
for path in (ROOT, CLIENT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from mip_jupyter_dev import jupyter_mcp_tools as tools


def run(coro):
    return asyncio.run(coro)


class FakeVariable:
    def __init__(self, code, label):
        self.code = code
        self.label = label

    def summary(self):
        return {"code": self.code, "label": self.label, "type": "integer"}


class FakeVariables:
    def search(self, query):
        return [FakeVariable("nihss", f"NIHSS {query}")]


class FakeDataModel:
    variables = FakeVariables()

    def summary(self):
        return {"code": "stroke", "version": "3.7", "n_variables": 1, "n_datasets": 1}

    def list_datasets(self):
        return [{"code": "ds", "label": "Dataset", "n_variables": 1}]

    def list_groups(self):
        return [{"code": "clinical", "label": "Clinical"}]

    def list_variables(self):
        return [{"code": "nihss", "label": "NIHSS", "type": "integer"}]


class FakeCatalog:
    def summaries(self):
        return [
            {"code": "stroke", "version": "3.7", "label": "Stroke"},
            {"code": "dementia", "version": "0.1", "label": "Dementia"},
        ]

    def data_model(self, code, version=None):
        self.last_lookup = (code, version)
        return FakeDataModel()


class FakeAlgorithm:
    def __init__(self, name, kind):
        self.name = name
        self.kind = kind

    def summary(self):
        return {"name": self.name, "label": self.name.title(), "type": self.kind, "desc": None}


class FakeAlgorithms:
    def list(self):
        return [FakeAlgorithm("describe", "statistics"), FakeAlgorithm("logistic_regression", "model")]


class FakeClient:
    def __init__(self):
        self._catalog = FakeCatalog()
        self._algorithms = FakeAlgorithms()

    def catalog(self):
        return self._catalog

    def algorithms(self):
        return self._algorithms


class TestJupyterMcpTools(unittest.TestCase):
    def _workspace(self):
        tmp = tempfile.TemporaryDirectory()
        workspace = Path(tmp.name) / "workspace"
        workspace.mkdir()
        (workspace / "docs").mkdir()
        return tmp, workspace

    def test_agent_docs_search_is_bounded_to_workspace_docs(self):
        tmp, workspace = self._workspace()
        self.addCleanup(tmp.cleanup)
        repo = workspace.parent
        agent_docs = repo / "agent-docs"
        (agent_docs / "llm" / "wiki").mkdir(parents=True)
        (agent_docs / "llm" / "wiki" / "00-agent-workspace.md").write_text(
            "# Agent Workspace Guide\n\n## Scratch\n\nUse scratch notebooks for NIHSS analysis.",
            encoding="utf-8",
        )
        (workspace / "docs" / "quickstart.md").write_text(
            "# Quickstart\n\nNIHSS variables are discovered through metadata summaries.",
            encoding="utf-8",
        )
        (workspace.parent / "outside.md").write_text("NIHSS SECRET_OUTSIDE", encoding="utf-8")

        with patch.dict(
            os.environ,
            {"MIP_JUPYTER_ROOT": str(workspace), "MIP_AGENT_DOCS": str(agent_docs)},
        ):
            guide = run(tools.agent_read_guide(topic="scratch"))
            result = run(tools.agent_search_docs("NIHSS", limit=1))

        serialized = json.dumps(result)
        self.assertTrue(guide["ok"])
        self.assertEqual(len(result["results"]), 1)
        self.assertTrue(result["results"][0]["path"].startswith("docs/"))
        self.assertNotIn("SECRET_OUTSIDE", serialized)
        self.assertLessEqual(len(result["results"][0]["snippet"]), tools.MAX_DOC_SNIPPET_CHARS)

    def test_notebook_outline_excludes_full_outputs_and_cell_read_limits_source(self):
        tmp, workspace = self._workspace()
        self.addCleanup(tmp.cleanup)
        notebook = workspace / "scratch" / "probe.ipynb"
        notebook.parent.mkdir()
        notebook.write_text(
            json.dumps(
                {
                    "cells": [
                        {"cell_type": "markdown", "metadata": {}, "source": "# Intro\n" + "x" * 80},
                        {
                            "cell_type": "code",
                            "execution_count": 1,
                            "metadata": {},
                            "source": "print('ok')",
                            "outputs": [
                                {"output_type": "stream", "name": "stdout", "text": "SECRET_OUTPUT" + "y" * 500}
                            ],
                        },
                    ],
                    "metadata": {},
                    "nbformat": 4,
                    "nbformat_minor": 5,
                }
            ),
            encoding="utf-8",
        )

        with patch.dict(os.environ, {"MIP_JUPYTER_ROOT": str(workspace)}):
            outline = run(tools.notebook_outline("scratch/probe.ipynb"))
            cell = run(tools.notebook_read_cell("scratch/probe.ipynb", 0, max_chars=10))

        self.assertEqual(outline["cell_count"], 2)
        self.assertNotIn("SECRET_OUTPUT", json.dumps(outline))
        self.assertEqual(cell["source"], "# Intro\nxx")
        self.assertTrue(cell["source_truncated"])

    def test_create_append_and_edit_notebook_under_workspace(self):
        tmp, workspace = self._workspace()
        self.addCleanup(tmp.cleanup)

        with patch.dict(os.environ, {"MIP_JUPYTER_ROOT": str(workspace)}):
            created = run(tools.create_notebook("scratch/mcp_probe.ipynb"))
            first = run(tools.append_markdown_cell("scratch/mcp_probe.ipynb", "# Probe"))
            second = run(tools.append_code_cell("scratch/mcp_probe.ipynb", "1 + 1"))
            edited = run(tools.edit_cell_by_index("scratch/mcp_probe.ipynb", 0, "# Updated", "markdown"))
            outline = run(tools.notebook_outline("scratch/mcp_probe.ipynb"))

        self.assertTrue(created["ok"])
        self.assertEqual(first["index"], 0)
        self.assertEqual(second["index"], 1)
        self.assertEqual(edited["cell_type"], "markdown")
        self.assertEqual(outline["cells"][0]["headings"], ["Updated"])
        self.assertTrue((workspace / "scratch" / "mcp_probe.ipynb").exists())

    def test_mip_env_status_does_not_expose_token_values(self):
        tmp, workspace = self._workspace()
        self.addCleanup(tmp.cleanup)
        secret = "TOP_SECRET_TOKEN"

        with patch.dict(
            os.environ,
            {"MIP_JUPYTER_ROOT": str(workspace), "PLATFORM_BACKEND_URL": "http://backend/services", "MIP_TOKEN": secret},
        ):
            status = run(tools.mip_env_status())

        serialized = json.dumps(status)
        self.assertTrue(status["backend_url_present"])
        self.assertTrue(status["token_present"])
        self.assertNotIn(secret, serialized)

    def test_mip_metadata_tools_use_mocked_client(self):
        fake_client = FakeClient()
        with patch("mip.Client.from_env", return_value=fake_client) as from_env:
            catalog = run(tools.mip_catalog_summary(limit=1))
            model = run(tools.mip_data_model_summary("stroke", version="3.7", include_variables=True))
            variables = run(tools.mip_search_variables("stroke", "NIHSS", version="3.7", limit=5))
            algorithms = run(tools.mip_algorithm_summary())

        self.assertEqual(from_env.call_count, 4)
        self.assertEqual(catalog["items"], [{"code": "stroke", "version": "3.7", "label": "Stroke"}])
        self.assertTrue(catalog["truncated"])
        self.assertEqual(model["summary"]["code"], "stroke")
        self.assertEqual(model["variables"][0]["code"], "nihss")
        self.assertEqual(variables["items"][0]["code"], "nihss")
        self.assertEqual(algorithms["counts_by_type"], {"statistics": 1, "model": 1})


if __name__ == "__main__":
    unittest.main()
