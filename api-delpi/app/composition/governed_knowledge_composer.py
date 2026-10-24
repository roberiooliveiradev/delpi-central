from app.application.use_cases.read_governed_technical_knowledge_use_case import (
    ReadGovernedTechnicalKnowledgeUseCase,
)
from app.infrastructure.knowledge.governed_knowledge_repository import GovernedKnowledgeRepository


def build_read_governed_technical_knowledge() -> ReadGovernedTechnicalKnowledgeUseCase:
    return ReadGovernedTechnicalKnowledgeUseCase(GovernedKnowledgeRepository())


def published_knowledge_topics() -> list[dict]:
    from app.application.use_cases.read_governed_technical_knowledge_use_case import KnowledgeReadError

    try:
        _, index, _ = GovernedKnowledgeRepository().load()
    except KnowledgeReadError:
        return []
    return index["topics"]
