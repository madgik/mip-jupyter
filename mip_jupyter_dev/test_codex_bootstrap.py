"""Tests for Codex bootstrap and qwen model catalog generation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mip_jupyter_dev import notebook as notebook_runner
from mip_jupyter_dev.codex_bootstrap import (
    DEFAULT_CODEX_MODEL,
    DEFAULT_CODEX_MODELS,
    DEFAULT_CODEX_PERSONA_ID,
    SCOPE_RULES,
    CodexSettings,
    bootstrap_codex,
    write_codex_config,
    write_codex_model_catalog,
)
from mip_jupyter_dev.mip_acp_persona import MIP_PERSONA_ID
from mip_jupyter_dev.mip_acp_persona import MIP_PERSONA_NAME
from mip_jupyter_dev.mip_acp_persona import VLLM_UNAVAILABLE_MESSAGE
from mip_jupyter_dev.mip_acp_persona import is_vllm_unavailable_error
from mip_jupyter_dev.mip_persona_manager import (
    ALLOWED_PERSONA_ENTRY_POINTS,
    MIP_PERSONA_MANAGER_CLASS,
    MipPersonaManager,
)
from mip_jupyter_dev.jupyter_mcp_config import build_config as build_mcp_config


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
    assert "recipes" in qwen["base_instructions"]
    assert SCOPE_RULES in qwen["base_instructions"]
    assert "first make the step sequence work in plain Python" in qwen["base_instructions"]


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


def test_vllm_unavailable_detection_matches_connection_failures() -> None:
    assert is_vllm_unavailable_error(ConnectionError("connection refused"))
    assert is_vllm_unavailable_error(RuntimeError("503 Service Unavailable from vLLM"))
    assert is_vllm_unavailable_error(TimeoutError("request timed out"))
    assert not is_vllm_unavailable_error(ValueError("invalid notebook path"))


def test_vllm_unavailable_message_is_user_facing() -> None:
    assert "Cohort Scout cannot reach the qwen vLLM model service" in VLLM_UNAVAILABLE_MESSAGE
    assert "MIP platform connection are unaffected" in VLLM_UNAVAILABLE_MESSAGE
    assert "CODEX_VLLM_BASE_URL" in VLLM_UNAVAILABLE_MESSAGE


def test_default_persona_is_cohort_scout() -> None:
    assert DEFAULT_CODEX_PERSONA_ID == MIP_PERSONA_ID
    assert MIP_PERSONA_NAME == "Cohort Scout"


def test_bootstrap_codex_writes_catalog_and_config(tmp_path: Path) -> None:
    settings = CodexSettings.from_env()
    codex_home = tmp_path / "codex-home"
    jupyter_config = tmp_path / "jupyter_ai_config.json"

    bootstrap_codex(codex_home, jupyter_config, settings)

    catalog = json.loads((codex_home / "model-catalog.json").read_text(encoding="utf-8"))
    assert len(catalog["models"]) == 1
    assert catalog["models"][0]["slug"] == "qwen36-nvfp4"
    assert MIP_PERSONA_NAME in catalog["models"][0]["base_instructions"]
    assert (codex_home / "config.toml").is_file()
    jupyter_config_data = json.loads(jupyter_config.read_text(encoding="utf-8"))
    assert jupyter_config_data["PersonaManager"]["default_persona_id"] == MIP_PERSONA_ID
    assert (
        jupyter_config_data["PersonaManagerExtension"]["persona_manager_class"]
        == MIP_PERSONA_MANAGER_CLASS
    )
    assert jupyter_config.is_file()


def test_mcp_config_uses_mip_persona_manager_only() -> None:
    config = build_mcp_config(mcp_port=3001)
    assert config["PersonaManager"]["default_persona_id"] == MIP_PERSONA_ID
    assert config["PersonaManagerExtension"]["persona_manager_class"] == MIP_PERSONA_MANAGER_CLASS


def test_mip_persona_manager_filters_third_party_entry_points(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from jupyter_ai_persona_manager.persona_manager import PersonaManager

    PersonaManager._ep_persona_classes = None

    def fake_load_all(_self) -> None:
        PersonaManager._ep_persona_classes = [
            {"module": "codex-acp", "persona_class": object(), "traceback": None},
            {"module": "claude-acp", "persona_class": object(), "traceback": None},
            {"module": "cohort-scout", "persona_class": object(), "traceback": None},
        ]

    monkeypatch.setattr(PersonaManager, "_init_ep_persona_classes", fake_load_all)

    manager = MipPersonaManager.__new__(MipPersonaManager)
    import logging

    manager.log = logging.getLogger("test")
    MipPersonaManager._init_ep_persona_classes(manager)

    loaded = PersonaManager._ep_persona_classes or []
    assert [item["module"] for item in loaded] == ["cohort-scout"]
    assert ALLOWED_PERSONA_ENTRY_POINTS == frozenset({"cohort-scout"})
    PersonaManager._ep_persona_classes = None
