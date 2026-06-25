"""Tests for Codex bootstrap and qwen model catalog generation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mip_jupyter_dev import notebook as notebook_runner
from mip_jupyter_dev.codex_bootstrap import (
    DEFAULT_CODEX_MODEL,
    DEFAULT_CODEX_MODELS,
    CodexSettings,
    bootstrap_codex,
    write_codex_config,
    write_codex_model_catalog,
)


@pytest.fixture(autouse=True)
def _clear_codex_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "CODEX_VLLM_MODEL",
        "CODEX_MODEL_CONTEXT_WINDOW",
        "CODEX_AUTO_COMPACT_TOKEN_LIMIT",
        "CODEX_ENABLE_NATIVE_JUPYTER_MCP",
        "CODEX_DISABLE_NATIVE_JUPYTER_MCP",
    ):
        monkeypatch.delenv(name, raising=False)


def test_catalog_defaults_to_qwen_only() -> None:
    assert DEFAULT_CODEX_MODELS == ("qwen36-nvfp4",)


def test_from_env_default_model_is_qwen() -> None:
    settings = CodexSettings.from_env()
    assert settings.model == DEFAULT_CODEX_MODEL
    assert settings.model == "qwen36-nvfp4"
    assert settings.context_window == 32768
    assert settings.auto_compact_limit == 28000


def test_from_env_invalid_model_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEX_VLLM_MODEL", "other-model")
    with pytest.raises(ValueError, match="supports only qwen36-nvfp4"):
        CodexSettings.from_env()


def test_model_catalog_contains_qwen_model_only(tmp_path: Path) -> None:
    settings = CodexSettings.from_env()
    catalog_path = tmp_path / "model-catalog.json"
    write_codex_model_catalog(catalog_path, settings)

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    slugs = [entry["slug"] for entry in catalog["models"]]
    assert slugs == ["qwen36-nvfp4"]

    qwen = catalog["models"][0]
    assert qwen["context_window"] == 32768


def test_config_toml_uses_default_qwen_model(tmp_path: Path) -> None:
    settings = CodexSettings.from_env()
    catalog_path = tmp_path / "model-catalog.json"
    config_path = tmp_path / "config.toml"
    write_codex_model_catalog(catalog_path, settings)
    write_codex_config(config_path, settings, catalog_path)

    config = config_path.read_text(encoding="utf-8")
    assert 'model = "qwen36-nvfp4"' in config
    assert "model_context_window = 32768" in config
    assert "model_auto_compact_token_limit = 28000" in config


def test_notebook_cli_context_overrides_are_used() -> None:
    args = notebook_runner._parser().parse_args(
        [
            "--mcp-port",
            "3123",
            "--codex-context-window",
            "4096",
            "--codex-auto-compact-limit",
            "3500",
        ]
    )

    settings = notebook_runner._codex_settings_from_args(args)

    assert settings.model == "qwen36-nvfp4"
    assert settings.catalog_models == ("qwen36-nvfp4",)
    assert settings.context_window == 4096
    assert settings.auto_compact_limit == 3500


def test_bootstrap_codex_writes_catalog_and_config(tmp_path: Path) -> None:
    settings = CodexSettings.from_env()
    codex_home = tmp_path / "codex-home"
    jupyter_config = tmp_path / "jupyter_ai_config.json"

    bootstrap_codex(codex_home, jupyter_config, settings)

    catalog = json.loads((codex_home / "model-catalog.json").read_text(encoding="utf-8"))
    assert len(catalog["models"]) == 1
    assert catalog["models"][0]["slug"] == "qwen36-nvfp4"
    assert (codex_home / "config.toml").is_file()
    assert jupyter_config.is_file()
