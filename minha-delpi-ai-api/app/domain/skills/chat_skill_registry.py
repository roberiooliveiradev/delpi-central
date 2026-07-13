from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import ClassVar

from app.domain.ports.chat_skill_repository_port import ChatSkillRepositoryPort
from app.domain.ports.external_action_repository_port import ExternalActionRepositoryPort
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_domain_config_service import ChatDomainConfigService

SQL_SKILL_KEY = "sql"
SQL_EXECUTION_PATH_TOKEN = "/data/sql"
COMPANY_KNOWLEDGE_SKILL_KEY = "company-knowledge"
TECHNICAL_DESCRIPTION_SKILL_KEY = "technical-description-delpi"
DRAWING_ANALYSIS_SKILL_KEY = "drawing-analysis-delpi"
DOCUMENT_VISION_SKILL_KEY = "document-vision-delpi"
QUALITY_ACTION_PLANS_SKILL_KEY = "quality-action-plans-delpi"
QUALITY_ACTION_PLANS_PATH_TOKEN = "/quality/action-plans"
DRAWING_ANALYSER_ACTION_ID = "get_product_analyser"
DRAWING_ANALYSER_PATH_TOKEN = "/analyser"


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
    catalog = ChatAssistantContentService.load_skills_catalog()
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


def _merge_db_and_json_skills(rows: list[dict]) -> tuple[ChatSkillDefinition, ...]:
    json_defs = list(_skills_from_json())
    json_by_key = {d.key: d for d in json_defs}

    db_defs = [_definition_from_row(row) for row in (rows or []) if isinstance(row, dict)]

    merged: list[ChatSkillDefinition] = []
    seen: set[str] = set()

    for definition in db_defs:
        if definition.key and definition.key not in seen:
            merged.append(definition)
            seen.add(definition.key)

    for key, definition in json_by_key.items():
        if key and key not in seen:
            merged.append(definition)
            seen.add(key)

    if merged:
        return tuple(merged)

    return _skills_from_json()


@lru_cache(maxsize=1)
def _skills() -> tuple[ChatSkillDefinition, ...]:
    repository = ChatSkillRegistry._skill_repository

    if repository is None:
        return _skills_from_json()

    try:
        return _merge_db_and_json_skills(repository.list_active())
    except Exception:
        return _skills_from_json()


class ChatSkillRegistry:
    _skill_repository: ClassVar[ChatSkillRepositoryPort | None] = None
    _external_action_repository: ClassVar[ExternalActionRepositoryPort | None] = None

    @classmethod
    def configure(
        cls,
        *,
        skill_repository: ChatSkillRepositoryPort,
        external_action_repository: ExternalActionRepositoryPort,
    ) -> None:
        cls._skill_repository = skill_repository
        cls._external_action_repository = external_action_repository
        invalidate_skill_cache()

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

            return PromptPolicyService._load_policy(definition.policy_file)

        return ""

    @classmethod
    def list_known_keys(cls) -> list[str]:
        return [item.key for item in _skills()]

    @classmethod
    def is_enabled(cls, agent_metadata: dict | None, skill_key: str) -> bool:
        normalized = str(skill_key or "").strip().lower()

        if normalized == "drawing-analyser":
            normalized = DRAWING_ANALYSIS_SKILL_KEY

        definition = cls.get(normalized)

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
        default_company_knowledge: bool = True,
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
            elif definition.key == COMPANY_KNOWLEDGE_SKILL_KEY and not has_agent:
                enabled = default_company_knowledge
            elif definition.key == COMPANY_KNOWLEDGE_SKILL_KEY and has_agent and not cls._has_explicit_config(
                agent_metadata,
                definition,
            ):
                enabled = default_company_knowledge
            elif definition.key == TECHNICAL_DESCRIPTION_SKILL_KEY and not has_agent:
                enabled = default_company_knowledge
            elif (
                definition.key == TECHNICAL_DESCRIPTION_SKILL_KEY
                and has_agent
                and not cls._has_explicit_config(agent_metadata, definition)
            ):
                enabled = default_company_knowledge
            elif (
                definition.key == DRAWING_ANALYSIS_SKILL_KEY
                and has_agent
                and not cls._has_explicit_config(agent_metadata, definition)
            ):
                enabled = cls._drawing_analysis_available(allowed)
            elif definition.key == DOCUMENT_VISION_SKILL_KEY:
                if not cls._has_explicit_config(agent_metadata, definition):
                    enabled = ChatDomainConfigService.chat_document_vision_enabled()
            elif (
                definition.key == QUALITY_ACTION_PLANS_SKILL_KEY
                and has_agent
                and not cls._has_explicit_config(agent_metadata, definition)
            ):
                enabled = cls._quality_action_plans_available(allowed)

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
        default_company_knowledge: bool = True,
    ) -> dict:
        bindings = cls.list_agent_bindings(
            agent_metadata=agent_metadata,
            allowed_action_ids=allowed_action_ids,
            has_agent=has_agent,
            default_sql_authoring=default_sql_authoring,
            default_company_knowledge=default_company_knowledge,
        )

        resolved = {
            "sqlAuthoring": False,
            "sqlExecutionAvailable": False,
            "companyKnowledge": False,
            "technicalDescription": False,
            "drawingAnalysis": False,
            "documentVision": False,
            "qualityActionPlans": False,
            "qualityActionPlansReadOnly": False,
        }

        for item in bindings:
            if item["skillKey"] == SQL_SKILL_KEY:
                resolved["sqlAuthoring"] = bool(item["enabled"])
                resolved["sqlExecutionAvailable"] = bool(
                    (item.get("derived") or {}).get("sqlExecutionAvailable")
                )
            if item["skillKey"] == COMPANY_KNOWLEDGE_SKILL_KEY:
                resolved["companyKnowledge"] = bool(item["enabled"])
            if item["skillKey"] == TECHNICAL_DESCRIPTION_SKILL_KEY:
                resolved["technicalDescription"] = bool(item["enabled"])
            if item["skillKey"] == DRAWING_ANALYSIS_SKILL_KEY:
                resolved["drawingAnalysis"] = bool(item["enabled"])
            if item["skillKey"] == DOCUMENT_VISION_SKILL_KEY:
                resolved["documentVision"] = bool(item["enabled"])
            if item["skillKey"] == QUALITY_ACTION_PLANS_SKILL_KEY:
                resolved["qualityActionPlans"] = bool(item["enabled"])

        if resolved["qualityActionPlans"]:
            from app.domain.services.chat_quality_action_plans_access_service import (
                ChatQualityActionPlansAccessService,
            )

            resolved["qualityActionPlansReadOnly"] = (
                ChatQualityActionPlansAccessService.resolve_read_only_mode(
                    allowed_action_ids
                )
            )
        else:
            resolved["qualityActionPlansReadOnly"] = False

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

        if skill_block is None and definition.key == DRAWING_ANALYSIS_SKILL_KEY:
            skill_block = skills.get("drawing-analyser")

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
    def _drawing_analysis_available(cls, allowed_action_ids: list[str]) -> bool:
        if not allowed_action_ids:
            return False

        allowed_set = {str(item).strip() for item in allowed_action_ids if str(item).strip()}

        if DRAWING_ANALYSER_ACTION_ID in allowed_set:
            return True

        operation_suffix = f".{DRAWING_ANALYSER_ACTION_ID}"

        if any(action_id.endswith(operation_suffix) for action_id in allowed_set):
            return True

        repository = cls._external_action_repository

        if repository is None:
            return False

        try:
            for action in repository.list_actions():
                action_id = str(action.get("actionId") or "").strip()

                if action_id not in allowed_set:
                    continue

                path = str(action.get("path") or "").lower()

                if DRAWING_ANALYSER_PATH_TOKEN in path:
                    return True
        except Exception:
            return False

        return False

    @classmethod
    def _quality_action_plans_available(cls, allowed_action_ids: list[str]) -> bool:
        if not allowed_action_ids:
            return False

        allowed_set = {str(item).strip() for item in allowed_action_ids if str(item).strip()}

        pac_operation_markers = (
            "list_quality_action_plans",
            "get_quality_action_plans_dashboard",
            "create_quality_action_plan",
        )

        if any(marker in action_id for action_id in allowed_set for marker in pac_operation_markers):
            return True

        repository = cls._external_action_repository

        if repository is None:
            return False

        try:
            for action in repository.list_actions():
                action_id = str(action.get("actionId") or "").strip()

                if action_id not in allowed_set:
                    continue

                path = str(action.get("path") or "").lower()

                if QUALITY_ACTION_PLANS_PATH_TOKEN in path:
                    return True
        except Exception:
            return False

        return False

    @classmethod
    def _sql_execution_available(cls, allowed_action_ids: list[str]) -> bool:
        if not allowed_action_ids:
            return False

        repository = cls._external_action_repository

        if repository is None:
            return False

        try:
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
