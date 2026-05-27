from __future__ import annotations

from app.infrastructure.config.settings import Settings

SQL_EXECUTION_PATH_TOKEN = "/data/sql"


class ChatAgentSkillsService:
    """Skills = comportamentos do LLM (prompt). Actions = execução via OpenAPI."""

    @classmethod
    def resolve(
        cls,
        *,
        agent_metadata: dict | None,
        allowed_action_ids: list[str] | None = None,
        has_agent: bool = False,
    ) -> dict:
        allowed = [str(item).strip() for item in (allowed_action_ids or []) if str(item).strip()]

        sql_authoring = cls._sql_authoring_enabled(agent_metadata, has_agent=has_agent)
        sql_execution = cls._sql_execution_available(allowed)

        return {
            "sqlAuthoring": sql_authoring,
            "sqlExecutionAvailable": sql_execution,
        }

    @classmethod
    def _sql_authoring_enabled(cls, agent_metadata: dict | None, *, has_agent: bool) -> bool:
        if isinstance(agent_metadata, dict):
            skills = agent_metadata.get("skills")

            if isinstance(skills, dict):
                sql_block = skills.get("sql")

                if isinstance(sql_block, dict) and "authoring" in sql_block:
                    return bool(sql_block.get("authoring"))

                if "sqlAuthoring" in skills:
                    return bool(skills.get("sqlAuthoring"))

        if not has_agent:
            return Settings.CHAT_DEFAULT_SQL_AUTHORING_SKILL

        return False

    @classmethod
    def _sql_execution_available(cls, allowed_action_ids: list[str]) -> bool:
        if not allowed_action_ids:
            return False

        try:
            from app.infrastructure.persistence.postgres_external_action_repository import (
                PostgresExternalActionRepository,
            )

            repository = PostgresExternalActionRepository()
            allowed_set = set(allowed_action_ids)

            for action in repository.list_actions():
                action_id = str(action.get("actionId") or "").strip()

                if action_id not in allowed_set:
                    continue

                path = str(action.get("path") or "").lower()

                if SQL_EXECUTION_PATH_TOKEN in path:
                    return True
        except Exception:
            return False

        return False
