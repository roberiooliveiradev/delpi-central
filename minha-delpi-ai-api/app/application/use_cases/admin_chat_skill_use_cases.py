from __future__ import annotations

from uuid import UUID

from app.domain.ports.chat_skill_repository_port import ChatSkillRepositoryPort
from app.domain.skills.chat_skill_registry import invalidate_skill_cache
from app.infrastructure.content.content_service import ContentService


def _default_skill_repository() -> ChatSkillRepositoryPort:
    from app.composition.repository_composer import make_chat_skill_repository

    return make_chat_skill_repository()


class ListAdminChatSkillsUseCase:
    def __init__(self, repository: ChatSkillRepositoryPort | None = None):
        self.repository = repository or _default_skill_repository()

    def execute(self, *, include_inactive: bool = True) -> list[dict]:
        # Bootstrapa skills "built-in" do catálogo embarcado (ex.: `company-knowledge`)
        # quando o banco ainda não foi populado (ambiente novo / migração pendente).
        # Isso garante consistência do runtime e permite gerenciar as skills via UI.
        existing = self.repository.list_all(include_inactive=True) or []
        existing_keys = {
            str(item.get("skillKey") or "").strip().lower()
            for item in existing
            if isinstance(item, dict)
        }

        catalog = ContentService.skills_catalog()
        for item in (catalog.get("skills") or []):
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or "").strip().lower()
            if not key or key in existing_keys:
                continue

            payload = {
                "skillKey": key,
                "label": item.get("label") or key,
                "description": item.get("description") or "",
                "policyFile": item.get("policyFile") or "",
                "metadataFlag": item.get("metadataFlag") or "enabled",
                "legacyMetadataFlag": item.get("legacyMetadataFlag"),
                "executionPathHint": item.get("executionPathHint"),
                "executionDerivedKey": item.get("executionDerivedKey"),
                "isActive": True,
                "sortOrder": int(item.get("sortOrder") or 0),
            }
            try:
                created = self.repository.create(payload)
                existing_keys.add(str(created.get("skillKey") or "").strip().lower())
            except Exception:
                # Ambiente pode ter concorrência/seed paralelo; ignore se já existir.
                pass

        if existing_keys:
            invalidate_skill_cache()

        return self.repository.list_all(include_inactive=include_inactive)


class CreateAdminChatSkillUseCase:
    def __init__(self, repository: ChatSkillRepositoryPort | None = None):
        self.repository = repository or _default_skill_repository()

    def execute(self, payload: dict) -> dict:
        result = self.repository.create(payload)
        invalidate_skill_cache()
        return result


class UpdateAdminChatSkillUseCase:
    def __init__(self, repository: ChatSkillRepositoryPort | None = None):
        self.repository = repository or _default_skill_repository()

    def execute(self, skill_id: str, payload: dict) -> dict | None:
        result = self.repository.update(UUID(skill_id), payload)
        invalidate_skill_cache()
        return result


class DeactivateAdminChatSkillUseCase:
    def __init__(self, repository: ChatSkillRepositoryPort | None = None):
        self.repository = repository or _default_skill_repository()

    def execute(self, skill_id: str) -> bool:
        result = self.repository.deactivate(UUID(skill_id))
        invalidate_skill_cache()
        return result
