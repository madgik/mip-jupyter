"""MIP-branded Jupyter AI persona backed by Codex ACP."""

from __future__ import annotations

from jupyter_ai_acp_client.acp_personas.codex import CodexAcpPersona
from jupyter_ai_persona_manager import PersonaDefaults

MIP_PERSONA_NAME = "Cohort Scout"
MIP_PERSONA_ID = "jupyter-ai-personas::mip_jupyter_dev::CohortScoutPersona"
MIP_PERSONA_DESCRIPTION = (
    "MIP notebook assistant for cohort discovery and federated analysis—not general chat."
)


class CohortScoutPersona(CodexAcpPersona):
    @property
    def defaults(self) -> PersonaDefaults:
        base = super().defaults
        return PersonaDefaults(
            name=MIP_PERSONA_NAME,
            description=MIP_PERSONA_DESCRIPTION,
            avatar_path=base.avatar_path,
            system_prompt=base.system_prompt,
        )
