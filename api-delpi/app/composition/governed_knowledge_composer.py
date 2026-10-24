from app.application.use_cases.read_governed_technical_knowledge_use_case import (
    ReadGovernedTechnicalKnowledgeUseCase,
)
from app.infrastructure.knowledge.governed_knowledge_repository import GovernedKnowledgeRepository


def build_read_governed_technical_knowledge() -> ReadGovernedTechnicalKnowledgeUseCase:
    return ReadGovernedTechnicalKnowledgeUseCase(GovernedKnowledgeRepository())


def published_knowledge_topics(corpus_version: int | None = None) -> list[dict]:
    from scripts.davi_governed_knowledge_bundle_lib import LATEST_CORPUS_VERSION
    from app.application.use_cases.read_governed_technical_knowledge_use_case import KnowledgeReadError

    version = corpus_version if corpus_version is not None else LATEST_CORPUS_VERSION
    try:
        _, index, _ = GovernedKnowledgeRepository().load(version)
    except KnowledgeReadError:
        return []
    return index["topics"]
