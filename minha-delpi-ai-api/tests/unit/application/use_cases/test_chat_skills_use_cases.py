from uuid import uuid4

from app.application.dto.upsert_chat_agent_skill_request import UpsertChatAgentSkillRequest
from app.application.use_cases.chat_skills_use_cases import (
    ListChatSkillCatalogUseCase,
    UpsertChatAgentSkillUseCase,
)
from app.domain.entities.chat_agent import ChatAgent


class FakeSkillsRepository:
    def __init__(self):
        self.metadata: dict = {}
        self.saved = False

    def upsert_skill(self, agent_id, user_id, skill_key, enabled, can_manage_official_agents=False):
        self.metadata = {"skills": {skill_key: {"authoring": enabled}}}
        self.saved = True
        return True


def test_list_catalog_use_case():
    catalog = ListChatSkillCatalogUseCase().execute()

    assert any(item["skillKey"] == "sql" for item in catalog)


def test_upsert_skill_use_case():
    repository = FakeSkillsRepository()
    use_case = UpsertChatAgentSkillUseCase(repository)

    saved = use_case.execute(
        UpsertChatAgentSkillRequest(
            user_id=str(uuid4()),
            agent_id=str(uuid4()),
            skill_key="sql",
            enabled=True,
        )
    )

    assert saved is True
    assert repository.saved is True
