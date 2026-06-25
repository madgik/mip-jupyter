"""Bootstrap Codex + Jupyter AI configuration for local and Hub single-user runtimes."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path

from .jupyter_mcp_config import build_config as build_mcp_config
from .jupyter_mcp_tools import SAFE_JUPYTER_MCP_TOOLS

DEFAULT_CODEX_BASE_URL = "http://100.92.46.71:8001/v1"
DEFAULT_CODEX_MODEL = "qwen36-nvfp4"
DEFAULT_CODEX_MODELS = (DEFAULT_CODEX_MODEL,)
DEFAULT_CODEX_PROVIDER = "north_vllm"
DEFAULT_CODEX_CONTEXT_WINDOW = 32768
DEFAULT_CODEX_AUTO_COMPACT_LIMIT = 28000
DEFAULT_CODEX_PERSONA_ID = "jupyter-ai-personas::jupyter_ai_acp_client::CodexAcpPersona"
DEFAULT_MCP_PORT = 3001

BASE_INSTRUCTIONS = (
    "You are Codex in JupyterLab for MIP analysis users. Start with agent_read_guide, "
    "then agent_search_docs for user help in docs/. Agent wiki lives outside the user "
    "workspace at MIP_AGENT_DOCS (not for end users). Use notebook_outline before "
    "notebook_read_cell, keep notebook work under scratch/ unless the user names "
    "another path, and use mip.Client.from_env() through the curated MIP metadata "
    "tools. Never call Exaflow directly, dump tokens, or use broad filesystem reads. "
    "If native MCP is unavailable, call the same tools through "
    "python -m mip_jupyter_dev.jupyter_mcp_cli; JUPYTER_MCP_URL is set."
)


@dataclass(frozen=True)
class VllmModelProfile:
    slug: str
    display_name: str
    description: str
    context_window: int
    auto_compact_limit: int
    priority: int


VLLM_MODEL_REGISTRY: dict[str, VllmModelProfile] = {
    "qwen36-nvfp4": VllmModelProfile(
        slug="qwen36-nvfp4",
        display_name="qwen36-nvfp4",
        description="Qwen 3.6 35B NVFP4 model served by vLLM for mip-jupyter.",
        context_window=32768,
        auto_compact_limit=28000,
        priority=0,
    ),
}


def _validate_qwen_model(model: str, *, source: str) -> None:
    if model != DEFAULT_CODEX_MODEL:
        raise ValueError(f"{source} supports only {DEFAULT_CODEX_MODEL}.")


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _active_context_window(model: str) -> int:
    profile = VLLM_MODEL_REGISTRY[model]
    if os.getenv("CODEX_MODEL_CONTEXT_WINDOW"):
        return int(os.getenv("CODEX_MODEL_CONTEXT_WINDOW", str(profile.context_window)))
    return profile.context_window


def _active_auto_compact_limit(model: str) -> int:
    profile = VLLM_MODEL_REGISTRY[model]
    if os.getenv("CODEX_AUTO_COMPACT_TOKEN_LIMIT"):
        return int(os.getenv("CODEX_AUTO_COMPACT_TOKEN_LIMIT", str(profile.auto_compact_limit)))
    return profile.auto_compact_limit


@dataclass(frozen=True)
class CodexSettings:
    base_url: str
    model: str
    catalog_models: tuple[str, ...]
    provider: str
    context_window: int
    auto_compact_limit: int
    mcp_port: int
    enable_native_jupyter_mcp: bool

    @classmethod
    def from_env(
        cls,
        *,
        mcp_port: int | None = None,
    ) -> CodexSettings:
        model = os.getenv("CODEX_VLLM_MODEL", DEFAULT_CODEX_MODEL)
        _validate_qwen_model(model, source="CODEX_VLLM_MODEL")
        return cls(
            base_url=os.getenv("CODEX_VLLM_BASE_URL", DEFAULT_CODEX_BASE_URL),
            model=model,
            catalog_models=DEFAULT_CODEX_MODELS,
            provider=os.getenv("CODEX_VLLM_PROVIDER", DEFAULT_CODEX_PROVIDER),
            context_window=_active_context_window(model),
            auto_compact_limit=_active_auto_compact_limit(model),
            mcp_port=mcp_port if mcp_port is not None else int(os.getenv("JUPYTER_MCP_PORT", str(DEFAULT_MCP_PORT))),
            enable_native_jupyter_mcp=_env_flag("CODEX_ENABLE_NATIVE_JUPYTER_MCP")
            and not _env_flag("CODEX_DISABLE_NATIVE_JUPYTER_MCP", default=True),
        )


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _catalog_entry(profile: VllmModelProfile, *, context_window: int) -> dict:
    return {
        "slug": profile.slug,
        "display_name": profile.display_name,
        "description": profile.description,
        "default_reasoning_level": "minimal",
        "supported_reasoning_levels": [
            {
                "effort": "minimal",
                "description": "Fast local inference with minimal reasoning.",
            },
            {
                "effort": "low",
                "description": "Light reasoning for coding and notebook assistance.",
            },
        ],
        "shell_type": "shell_command",
        "visibility": "list",
        "supported_in_api": True,
        "priority": profile.priority,
        "additional_speed_tiers": [],
        "service_tiers": [],
        "availability_nux": None,
        "upgrade": None,
        "base_instructions": BASE_INSTRUCTIONS,
        "supports_reasoning_summaries": False,
        "default_reasoning_summary": "none",
        "support_verbosity": False,
        "default_verbosity": "low",
        "apply_patch_tool_type": None,
        "web_search_tool_type": "text_and_image",
        "truncation_policy": {"mode": "tokens", "limit": 10000},
        "supports_parallel_tool_calls": False,
        "supports_image_detail_original": False,
        "context_window": context_window,
        "max_context_window": context_window,
        "effective_context_window_percent": 95,
        "experimental_supported_tools": [],
        "input_modalities": ["text"],
        "supports_search_tool": False,
        "use_responses_lite": True,
    }


def write_codex_model_catalog(path: Path, settings: CodexSettings) -> None:
    entries = []
    for slug in settings.catalog_models:
        profile = VLLM_MODEL_REGISTRY[slug]
        context_window = settings.context_window if slug == settings.model else profile.context_window
        entries.append(_catalog_entry(profile, context_window=context_window))
    entries.sort(key=lambda entry: entry["priority"])
    _write_json(path, {"models": entries})


def write_codex_acp_wrapper(path: Path, executable: str) -> None:
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


def write_codex_config(path: Path, settings: CodexSettings, model_catalog_path: Path) -> None:
    provider = settings.provider
    config = (
        f'model = "{settings.model}"\n'
        f'model_provider = "{provider}"\n'
        f'model_catalog_json = "{model_catalog_path}"\n'
        f"model_context_window = {settings.context_window}\n"
        f"model_auto_compact_token_limit = {settings.auto_compact_limit}\n"
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
        f'base_url = "{settings.base_url}"\n'
        'wire_api = "responses"\n'
    )
    path.write_text(config, encoding="utf-8")


def build_jupyter_ai_config(settings: CodexSettings) -> dict:
    persona_manager_config: dict = {"default_persona_id": DEFAULT_CODEX_PERSONA_ID}
    if not settings.enable_native_jupyter_mcp:
        persona_manager_config["builtin_mcp_servers"] = []
    config = build_mcp_config(mcp_port=settings.mcp_port)
    config["PersonaManager"] = persona_manager_config
    config["MCPExtensionApp"]["mcp_tools"] = SAFE_JUPYTER_MCP_TOOLS
    return config


def bootstrap_codex(
    codex_home: Path,
    jupyter_ai_config: Path,
    settings: CodexSettings,
) -> Path | None:
    """Write Codex and Jupyter AI config. Returns codex-acp wrapper bin dir for PATH."""
    codex_home.mkdir(parents=True, exist_ok=True)
    model_catalog_path = codex_home / "model-catalog.json"
    write_codex_model_catalog(model_catalog_path, settings)
    write_codex_config(codex_home / "config.toml", settings, model_catalog_path)

    jupyter_ai_config.parent.mkdir(parents=True, exist_ok=True)
    _write_json(jupyter_ai_config, build_jupyter_ai_config(settings))

    codex_acp_path = shutil.which("codex-acp")
    if not codex_acp_path:
        return None
    wrapper = codex_home / "bin" / "codex-acp"
    write_codex_acp_wrapper(wrapper, codex_acp_path)
    return wrapper.parent


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap Codex + Jupyter AI for mip-jupyter.")
    parser.add_argument("codex_home", help="Directory for CODEX_HOME (config.toml, catalog)")
    parser.add_argument("jupyter_ai_config", help="Output JupyterLab JSON config path")
    parser.add_argument("--mcp-port", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not os.getenv("CODEX_VLLM_BASE_URL"):
        raise SystemExit("CODEX_VLLM_BASE_URL must be set to bootstrap Codex.")
    settings = CodexSettings.from_env(mcp_port=args.mcp_port)
    wrapper_bin = bootstrap_codex(Path(args.codex_home), Path(args.jupyter_ai_config), settings)
    if wrapper_bin is None:
        print("warning: codex-acp not found on PATH; Jupyter AI Codex persona may not start", flush=True)
    else:
        print(f"codex-acp wrapper: {wrapper_bin / 'codex-acp'}", flush=True)
    print(f"CODEX_HOME={args.codex_home}", flush=True)
    print(f"Jupyter AI config: {args.jupyter_ai_config}", flush=True)
    print(f"Codex base_url: {settings.base_url}", flush=True)
    print(f"Codex model: {settings.model}", flush=True)
    print(f"Codex catalog models: {', '.join(settings.catalog_models)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
