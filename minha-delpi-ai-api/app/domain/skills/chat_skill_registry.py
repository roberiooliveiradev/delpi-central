from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from app.infrastructure.content.content_service import ContentService

SQL_SKILL_KEY = "sql"
SQL_EXECUTION_PATH_TOKEN = "/data/sql"


@dataclass(frozen=True)
class ChatSkillDefinition:
    """Definição de uma skill no catálogo da plataforma."""

    key: str
    label: str
    description: str
    policy_file: str
    metadata_flag: str
    legacy_metadata_flag: str | None = None
    execution_path_hint: str | None = None
    execution_derived_key: str | None = None
    policy_content: str | None = None
    catalog_id: str | None = None
    is_active: bool = True


def invalidate_skill_cache() -> None:
    _skills.cache_clear()


def _skills_from_json() -> tuple[ChatSkillDefinition, ...]:
    catalog = ContentService.skills_catalog()
    items = catalog.get("skills") or []
    parsed: list[ChatSkillDefinition] = []

    for item in items:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or "").strip().lower()
        if not key:
            continue
        parsed.append(
            ChatSkillDefinition(
                key=key,
                label=str(item.get("label") or key),
                description=str(item.get("description") or ""),
                policy_file=str(item.get("policyFile") or ""),
                metadata_flag=str(item.get("metadataFlag") or "enabled"),
                legacy_metadata_flag=(
                    str(item["legacyMetadataFlag"])
                    if item.get("legacyMetadataFlag")
                    else None
                ),
                execution_path_hint=(
                    str(item["executionPathHint"]) if item.get("executionPathHint") else None
                ),
                execution_derived_key=(
                    str(item["executionDerivedKey"]) if item.get("executionDerivedKey") else None
                ),
            )
        )

    return tuple(parsed)


def _definition_from_row(row: dict) -> ChatSkillDefinition:
    return ChatSkillDefinition(
        key=str(row.get("skillKey") or "").strip().lower(),
        label=str(row.get("label") or ""),
        description=str(row.get("description") or ""),
        policy_file=str(row.get("policyFile") or ""),
        metadata_flag=str(row.get("metadataFlag") or "enabled"),
        legacy_metadata_flag=row.get("legacyMetadataFlag"),
        execution_path_hint=row.get("executionPathHint"),
        execution_derived_key=row.get("executionDerivedKey"),
        policy_content=row.get("policyContent"),
        catalog_id=row.get("id"),
        is_active=bool(row.get("isActive", True)),
    )


@lru_cache(maxsize=1)
def _skills() -> tuple[ChatSkillDefinition, ...]:
    try:
        from flask import has_app_context

        if has_app_context():
            from app.infrastructure.persistence.postgres_chat_skill_repository import (
                PostgresChatSkillRepository,
            )

            rows = PostgresChatSkillRepository().list_active()

            if rows:
                return tuple(_definition_from_row(row) for row in rows)
    except Exception:
        pass

    return _skills_from_json()


class ChatSkillRegistry:
    @classmethod
    def list_catalog(cls) -> list[dict]:
        return [cls._definition_to_catalog(item) for item in _skills()]

    @classmethod
    def get(cls, skill_key: str) -> ChatSkillDefinition | None:
        normalized = str(skill_key or "").strip().lower()

        for item in _skills():
            if item.key == normalized:
                return item

        return None

    @classmethod
    def get_policy_content(cls, skill_key: str) -> str:
        definition = cls.get(skill_key)

        if not definition:
            return ""

        if definition.policy_content and definition.policy_content.strip():
            return definition.policy_content.strip()

        if definition.policy_file:
            from app.domain.services.prompt_policy_service import PromptPolicyService

            return PromptPolicyService._load_policy(definition.policy_file, "")

        return ""

    @classmethod
    def list_known_keys(cls) -> list[str]:
        return [item.key for item in _skills()]

    @classmethod
    def is_enabled(cls, agent_metadata: dict | None, skill_key: str) -> bool:
        definition = cls.get(skill_key)

        if not definition:
            return False

        return cls._read_enabled(agent_metadata, definition)

    @classmethod
    def set_enabled(cls, agent_metadata: dict | None, skill_key: str, enabled: bool) -> dict:
        definition = cls.get(skill_key)

        if not definition:
            raise ValueError(f"Unknown skill key: {skill_key}")

        metadata = dict(agent_metadata or {})
        skills = dict(metadata.get("skills") or {}) if isinstance(metadata.get("skills"), dict) else {}
        skill_block = dict(skills.get(definition.key) or {}) if isinstance(skills.get(definition.key), dict) else {}

        skill_block[definition.metadata_flag] = bool(enabled)
        skills[definition.key] = skill_block

        if definition.legacy_metadata_flag:
            skills[definition.legacy_metadata_flag] = bool(enabled)

        metadata["skills"] = skills
        return metadata

    @classmethod
    def list_agent_bindings(
        cls,
        *,
        agent_metadata: dict | None,
        allowed_action_ids: list[str] | None = None,
        has_agent: bool = False,
        default_sql_authoring: bool = False,
    ) -> list[dict]:
        allowed = [str(item).strip() for item in (allowed_action_ids or []) if str(item).strip()]
        bindings: list[dict] = []

        for definition in _skills():
            enabled = cls._read_enabled(agent_metadata, definition)

            if definition.key == SQL_SKILL_KEY and not has_agent:
                enabled = default_sql_authoring
            elif definition.key == SQL_SKILL_KEY and has_agent and not cls._has_explicit_config(
                agent_metadata,
                definition,
            ):
                enabled = False

            derived: dict[str, bool] = {}

            if definition.execution_derived_key == "sqlExecutionAvailable":
                derived["sqlExecutionAvailable"] = cls._sql_execution_available(allowed)

            bindings.append(
                {
                    "skillKey": definition.key,
                    "label": definition.label,
                    "description": definition.description,
                    "policyFile": definition.policy_file,
                    "enabled": enabled,
                    "executionHint": definition.execution_path_hint,
                    "derived": derived,
                }
            )

        return bindings

    @classmethod
    def resolve_runtime_flags(
        cls,
        *,
        agent_metadata: dict | None,
        allowed_action_ids: list[str] | None = None,
        has_agent: bool = False,
        default_sql_authoring: bool = False,
    ) -> dict:
        bindings = cls.list_agent_bindings(
            agent_metadata=agent_metadata,
            allowed_action_ids=allowed_action_ids,
            has_agent=has_agent,
            default_sql_authoring=default_sql_authoring,
        )

        resolved = {
            "sqlAuthoring": False,
            "sqlExecutionAvailable": False,
        }

        for item in bindings:
            if item["skillKey"] == SQL_SKILL_KEY:
                resolved["sqlAuthoring"] = bool(item["enabled"])
                resolved["sqlExecutionAvailable"] = bool(
                    (item.get("derived") or {}).get("sqlExecutionAvailable")
                )

        return resolved

    @classmethod
    def _definition_to_catalog(cls, definition: ChatSkillDefinition) -> dict:
        payload = {
            "skillKey": definition.key,
            "label": definition.label,
            "description": definition.description,
            "policyFile": definition.policy_file,
            "metadataFlag": definition.metadata_flag,
            "executionHint": definition.execution_path_hint,
        }

        if definition.catalog_id:
            payload["id"] = definition.catalog_id

        return payload

    @classmethod
    def _read_enabled(cls, agent_metadata: dict | None, definition: ChatSkillDefinition) -> bool:
        if not isinstance(agent_metadata, dict):
            return False

        skills = agent_metadata.get("skills")

        if not isinstance(skills, dict):
            return False

        skill_block = skills.get(definition.key)

        if isinstance(skill_block, dict) and definition.metadata_flag in skill_block:
            return bool(skill_block.get(definition.metadata_flag))

        if definition.legacy_metadata_flag and definition.legacy_metadata_flag in skills:
            return bool(skills.get(definition.legacy_metadata_flag))

        return False

    @classmethod
    def _has_explicit_config(cls, agent_metadata: dict | None, definition: ChatSkillDefinition) -> bool:
        if not isinstance(agent_metadata, dict):
            return False

        skills = agent_metadata.get("skills")

        if not isinstance(skills, dict):
            return False

        skill_block = skills.get(definition.key)

        if isinstance(skill_block, dict) and definition.metadata_flag in skill_block:
            return True

        if definition.legacy_metadata_flag and definition.legacy_metadata_flag in skills:
            return True

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
