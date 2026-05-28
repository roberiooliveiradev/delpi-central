from __future__ import annotations

from app.domain.skills.chat_skill_registry import ChatSkillRegistry
from app.infrastructure.config.settings import Settings


class ChatAgentSkillsService:
    """Skills = comportamentos do LLM (prompt). Actions = execução via OpenAPI."""

    @classmethod
    def preserves_rag_on_fast_path(cls, skills: dict | None) -> bool:
        """Skill de conhecimento da empresa exige RAG mesmo em mensagens curtas (fast path)."""
        return bool((skills or {}).get("companyKnowledge"))

    @classmethod
    def resolve(
        cls,
        *,
        agent_metadata: dict | None,
        allowed_action_ids: list[str] | None = None,
        has_agent: bool = False,
    ) -> dict:
        return ChatSkillRegistry.resolve_runtime_flags(
            agent_metadata=agent_metadata,
            allowed_action_ids=allowed_action_ids,
            has_agent=has_agent,
            default_sql_authoring=Settings.CHAT_DEFAULT_SQL_AUTHORING_SKILL,
            default_company_knowledge=Settings.CHAT_DEFAULT_COMPANY_KNOWLEDGE_SKILL,
        )
