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
from .mip_acp_persona import MIP_PERSONA_ID
from .mip_acp_persona import MIP_PERSONA_NAME
from .mip_persona_manager import build_persona_manager_config

MIP_CONTEXT = (
    "MIP (Medical Informatics Platform) is a federated clinical research platform. "
    "Hospital sites keep patient data locally; use the pre-installed mip client in "
    "Jupyter to discover authorized metadata, define cohorts, and run federated analyses."
)

USER_FACING_RULES = (
    "Use plain product language: say 'the MIP platform', 'your connection', 'catalog', "
    "or 'analysis run'. Do not expose internal routes, URLs, infrastructure, or "
    "environment variable names unless developer or operator setup is requested. "
    "For connection issues, point to Welcome.ipynb, docs/troubleshooting.md, or "
    "the platform administrator."
)

SCOPE_RULES = (
    "Stay in scope: MIP JupyterLab, notebooks, the mip client, catalog, cohorts, "
    "pipelines, results, workspace docs, and supporting Python or statistics. For "
    "unrelated requests such as recipes, general knowledge, personal medical advice, "
    "or unrelated projects, do not call tools; refuse briefly as Cohort Scout and "
    "redirect to MIP notebook help. Do not invent catalog data."
)

MCP_CLI_RULES = (
    "NOTEBOOK AND MIP TOOLS (shell bridge): Use jupyter-mcp or python -m "
    "mip_jupyter_dev.jupyter_mcp_cli for notebook, wiki, user-doc, and MIP metadata "
    "actions. In shell-bridge mode, never call native mcp__* tools and never create "
    "or edit .ipynb files by writing JSON or direct filesystem edits. Read only the "
    "guide, routed wiki page, or user docs needed for the task. Retry once only for "
    "transient read failures (read-guide, search-docs, notebook-outline, read-cell, "
    "scratch-list, scratch-read, mip-* summaries). Never retry write commands "
    "(append-code, scratch-append-lines, scratch-to-notebook) without scratch-list or "
    "notebook-outline first."
)

PRIVACY_RULES = (
    "Never expose row-level patient data, identifiers, tokens, or raw execution "
    "outputs. Report only authorized aggregate metadata and analysis results."
)

ROUTING_RULES = (
    "Read read-guide --page index to pick the task wiki page; load analysis-specific "
    "rules from that routed page only."
)

NATIVE_MCP_RULES = (
    "NOTEBOOK AND MIP TOOLS (native MCP): Use the configured Jupyter MCP tools for "
    "notebook, wiki, user-doc, and MIP metadata actions. Never create or edit .ipynb "
    "files by writing JSON or direct filesystem edits."
)

TOOL_PAYLOAD_RULES = (
    "Keep tool args small JSON. No write_stdin/heredocs/shell file writes. "
    "Use scratch-copy-template, scratch-append-lines, scratch-replace-snippet, "
    "scratch-to-notebook, append-code."
)

PLAIN_PYTHON_RULES = (
    "Novel/multi-step: scratch-copy-template from examples/algorithm_examples.py, "
    "small scratch edits, verify with python scratch/<name>.py, then scratch-to-notebook."
)

FEDERATED_RULES = (
    "Federated only: dm.datasets['SSR']; never mix SSR with SSR-even/odd. Run "
    "stroke_preflight before inference. Use pipeline.available_algorithms() and "
    "typed Pipeline methods; signatures in examples/algorithm_examples.py. "
    "No inputdata/to_frame/sklearn on rows."
)

EXPLORATION_RULES = (
    "Exploration: read-guide agent-exploration; scratch-init on turn 1; "
    "scratch-list before new scripts; scratch-log-bottleneck after each step; "
    "max 20 lines per scratch edit."
)

NOVEL_STROKE_RULES = (
    "Novel Stroke: read-guide recipes/stroke-analysis novel, preflight, one hypothesis, "
    "scratch-copy-template from examples/algorithm_examples.py, trim to one analysis, "
    "run script, scratch-to-notebook. OR (95% CI) primary; secondary exploratory."
)


def build_base_instructions(*, enable_native_jupyter_mcp: bool = False) -> str:
    tool_rules = NATIVE_MCP_RULES if enable_native_jupyter_mcp else MCP_CLI_RULES
    return (
        f"You are {MIP_PERSONA_NAME} in JupyterLab for MIP analysis users. {MIP_CONTEXT} "
        f"{SCOPE_RULES} {USER_FACING_RULES} {PRIVACY_RULES} {tool_rules} {TOOL_PAYLOAD_RULES} "
        f"{ROUTING_RULES} Keep new work under scratch/, use curated MIP metadata tools, "
        "and avoid broad filesystem reads."
    )


BASE_INSTRUCTIONS = build_base_instructions()

DEFAULT_CODEX_BASE_URL = "http://100.92.46.71:8001/v1"
DEFAULT_CODEX_MODEL = "nemotron3-super-nvfp4"
DEFAULT_CODEX_PROVIDER = "vllm"
DEFAULT_CODEX_CONTEXT_WINDOW = 131072
DEFAULT_CODEX_AUTO_COMPACT_LIMIT = 112000
DEFAULT_CODEX_REASONING_EFFORT = "medium"
SUPPORTED_CODEX_REASONING_EFFORTS = frozenset({"minimal", "low", "medium"})
DEFAULT_CODEX_PERSONA_ID = MIP_PERSONA_ID
DEFAULT_MCP_PORT = 3001

@dataclass(frozen=True)
class VllmModelProfile:
    slug: str
    display_name: str
    description: str
    context_window: int
    auto_compact_limit: int
    priority: int


VLLM_MODEL_REGISTRY: dict[str, VllmModelProfile] = {
    "nemotron3-super-nvfp4": VllmModelProfile(
        slug="nemotron3-super-nvfp4",
        display_name="nemotron3-super-nvfp4",
        description="NVIDIA Nemotron 3 Super NVFP4 model served by vLLM for mip-jupyter.",
        context_window=131072,
        auto_compact_limit=112000,
        priority=0,
    ),
}

DEFAULT_CODEX_MODELS = (DEFAULT_CODEX_MODEL,)


def _validate_vllm_model(model: str, *, source: str) -> None:
    if model not in VLLM_MODEL_REGISTRY:
        supported = ", ".join(DEFAULT_CODEX_MODELS)
        raise ValueError(f"{source} must be one of: {supported}.")


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


def _active_reasoning_effort() -> str:
    effort = os.getenv("CODEX_REASONING_EFFORT", DEFAULT_CODEX_REASONING_EFFORT).strip().lower()
    if effort not in SUPPORTED_CODEX_REASONING_EFFORTS:
        supported = ", ".join(sorted(SUPPORTED_CODEX_REASONING_EFFORTS))
        raise ValueError(f"CODEX_REASONING_EFFORT must be one of: {supported}.")
    return effort


@dataclass(frozen=True)
class CodexSettings:
    base_url: str
    model: str
    catalog_models: tuple[str, ...]
    provider: str
    context_window: int
    auto_compact_limit: int
    reasoning_effort: str
    mcp_port: int
    enable_native_jupyter_mcp: bool

    @classmethod
    def from_env(
        cls,
        *,
        mcp_port: int | None = None,
    ) -> CodexSettings:
        model = os.getenv("CODEX_VLLM_MODEL", DEFAULT_CODEX_MODEL)
        _validate_vllm_model(model, source="CODEX_VLLM_MODEL")
        return cls(
            base_url=os.getenv("CODEX_VLLM_BASE_URL", DEFAULT_CODEX_BASE_URL),
            model=model,
            catalog_models=DEFAULT_CODEX_MODELS,
            provider=os.getenv("CODEX_VLLM_PROVIDER", DEFAULT_CODEX_PROVIDER),
            context_window=_active_context_window(model),
            auto_compact_limit=_active_auto_compact_limit(model),
            reasoning_effort=_active_reasoning_effort(),
            mcp_port=mcp_port if mcp_port is not None else int(os.getenv("JUPYTER_MCP_PORT", str(DEFAULT_MCP_PORT))),
            enable_native_jupyter_mcp=_env_flag("CODEX_ENABLE_NATIVE_JUPYTER_MCP")
            and not _env_flag("CODEX_DISABLE_NATIVE_JUPYTER_MCP"),
        )


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _catalog_entry(
    profile: VllmModelProfile,
    *,
    context_window: int,
    base_instructions: str,
    reasoning_effort: str,
) -> dict:
    return {
        "slug": profile.slug,
        "display_name": profile.display_name,
        "description": profile.description,
        "default_reasoning_level": reasoning_effort,
        "supported_reasoning_levels": [
            {
                "effort": "minimal",
                "description": "Fast local inference with minimal reasoning.",
            },
            {
                "effort": "low",
                "description": "Light reasoning for coding and notebook assistance.",
            },
            {
                "effort": "medium",
                "description": "Deeper reasoning for multi-step exploration and audits.",
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
        "base_instructions": base_instructions,
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
    base_instructions = build_base_instructions(
        enable_native_jupyter_mcp=settings.enable_native_jupyter_mcp
    )
    for slug in settings.catalog_models:
        profile = VLLM_MODEL_REGISTRY[slug]
        context_window = settings.context_window if slug == settings.model else profile.context_window
        entries.append(
            _catalog_entry(
                profile,
                context_window=context_window,
                base_instructions=base_instructions,
                reasoning_effort=settings.reasoning_effort,
            )
        )
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


def write_jupyter_mcp_cli_wrapper(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    script = "#!/bin/sh\nexec python -m mip_jupyter_dev.jupyter_mcp_cli \"$@\"\n"
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)


def write_shell_guard_wrapper(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    script = (
        "#!/bin/sh\n"
        "validate_command_args() {\n"
        "  while [ $# -gt 0 ]; do\n"
        "    case \"$1\" in\n"
        "      -c|-[!-]*c*)\n"
        "        [ -n \"$2\" ] || return 0\n"
        "        python -m mip_jupyter_dev.shell_guard --validate \"$2\"\n"
        "        return $?\n"
        "        ;;\n"
        "    esac\n"
        "    shift\n"
        "  done\n"
        "}\n"
        "validate_command_args \"$@\" || exit 1\n"
        "exec /bin/bash \"$@\"\n"
    )
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)


def write_codex_config(path: Path, settings: CodexSettings, model_catalog_path: Path) -> None:
    provider = settings.provider
    mcp_server_config = ""
    if settings.enable_native_jupyter_mcp:
        mcp_server_config = (
            "\n[mcp_servers.\"Jupyter MCP Server\"]\n"
            f'url = "http://127.0.0.1:{settings.mcp_port}/mcp"\n'
        )
    config = (
        f'model = "{settings.model}"\n'
        f'model_provider = "{provider}"\n'
        f'model_catalog_json = "{model_catalog_path}"\n'
        f"model_context_window = {settings.context_window}\n"
        f"model_auto_compact_token_limit = {settings.auto_compact_limit}\n"
        f'model_reasoning_effort = "{settings.reasoning_effort}"\n'
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
        'name = "vLLM"\n'
        f'base_url = "{settings.base_url}"\n'
        'wire_api = "responses"\n'
        f"{mcp_server_config}"
    )
    path.write_text(config, encoding="utf-8")


def build_jupyter_ai_config(settings: CodexSettings) -> dict:
    if settings.enable_native_jupyter_mcp:
        builtin_mcp_servers: list | None = None
    else:
        builtin_mcp_servers = []
    config = build_mcp_config(mcp_port=settings.mcp_port)
    config.update(
        build_persona_manager_config(
            default_persona_id=DEFAULT_CODEX_PERSONA_ID,
            builtin_mcp_servers=builtin_mcp_servers,
        )
    )
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

    write_jupyter_mcp_cli_wrapper(codex_home / "bin" / "jupyter-mcp")
    write_shell_guard_wrapper(codex_home / "bin" / "mip-shell-guard")

    codex_acp_path = shutil.which("codex-acp")
    if not codex_acp_path:
        return codex_home / "bin"
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
    print(f"Codex reasoning effort: {settings.reasoning_effort}", flush=True)
    print(f"Codex catalog models: {', '.join(settings.catalog_models)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
