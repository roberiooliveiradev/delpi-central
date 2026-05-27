from __future__ import annotations

from uuid import UUID

from app.domain.skills.chat_skill_registry import invalidate_skill_cache
from app.infrastructure.persistence.postgres_chat_skill_repository import PostgresChatSkillRepository


class ListAdminChatSkillsUseCase:
    def __init__(self, repository: PostgresChatSkillRepository | None = None):
        self.repository = repository or PostgresChatSkillRepository()

    def execute(self, *, include_inactive: bool = True) -> list[dict]:
        return self.repository.list_all(include_inactive=include_inactive)


class CreateAdminChatSkillUseCase:
    def __init__(self, repository: PostgresChatSkillRepository | None = None):
        self.repository = repository or PostgresChatSkillRepository()

    def execute(self, payload: dict) -> dict:
        result = self.repository.create(payload)
        invalidate_skill_cache()
        return result


class UpdateAdminChatSkillUseCase:
    def __init__(self, repository: PostgresChatSkillRepository | None = None):
        self.repository = repository or PostgresChatSkillRepository()

    def execute(self, skill_id: str, payload: dict) -> dict | None:
        result = self.repository.update(UUID(skill_id), payload)
        invalidate_skill_cache()
        return result


class DeactivateAdminChatSkillUseCase:
    def __init__(self, repository: PostgresChatSkillRepository | None = None):
        self.repository = repository or PostgresChatSkillRepository()

    def execute(self, skill_id: str) -> bool:
        result = self.repository.deactivate(UUID(skill_id))
        invalidate_skill_cache()
        return result
