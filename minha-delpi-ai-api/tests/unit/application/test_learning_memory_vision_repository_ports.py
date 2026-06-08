import ast
from pathlib import Path
from unittest.mock import Mock

from app.application.services.chat_document_vision_service import ChatDocumentVisionService
from app.application.services.chat_knowledge_candidate_service import (
    ChatKnowledgeCandidateService,
)
from app.application.use_cases.get_admin_learning_summary_use_case import (
    GetAdminLearningSummaryUseCase,
)
from app.domain.ports.chat_attachment_repository_port import ChatAttachmentRepositoryPort
from app.domain.ports.evaluation_case_repository_port import EvaluationCaseRepositoryPort
from app.domain.ports.fine_tuning_repository_port import FineTuningRepositoryPort
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort
from app.domain.ports.learning_candidate_repository_port import LearningCandidateRepositoryPort
from app.domain.ports.memory_item_repository_port import MemoryItemRepositoryPort
from app.domain.ports.vocabulary_term_repository_port import VocabularyTermRepositoryPort

_LEARNING_MEMORY_VISION_MODULES = [
    "app/application/services/chat_fine_tuning_service.py",
    "app/application/services/chat_knowledge_candidate_service.py",
    "app/application/services/chat_user_memory_service.py",
    "app/application/services/chat_memory_knowledge_index_service.py",
    "app/application/services/chat_glossary_knowledge_index_service.py",
    "app/application/services/chat_glossary_retrieval_service.py",
    "app/application/services/chat_learned_normalization_service.py",
    "app/application/services/chat_learning_promotion_gate_service.py",
    "app/application/services/chat_evaluation_case_service.py",
    "app/application/services/chat_document_vision_service.py",
    "app/application/use_cases/get_admin_learning_summary_use_case.py",
    "app/application/use_cases/chat_learning_use_cases.py",
    "app/application/use_cases/chat_user_memory_use_cases.py",
]


def test_learning_memory_vision_modules_have_no_postgres_imports():
    for rel_path in _LEARNING_MEMORY_VISION_MODULES:
        tree = ast.parse(Path(rel_path).read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "postgres" in node.module:
                raise AssertionError(f"Postgres import in {rel_path}: {node.module}")


def test_get_admin_learning_summary_delegates_to_ports():
    candidate_repository = Mock(spec=LearningCandidateRepositoryPort)
    vocabulary_repository = Mock(spec=VocabularyTermRepositoryPort)
    memory_repository = Mock(spec=MemoryItemRepositoryPort)
    evaluation_repository = Mock(spec=EvaluationCaseRepositoryPort)
    fine_tuning_repository = Mock(spec=FineTuningRepositoryPort)
    knowledge_repository = Mock(spec=KnowledgeRepositoryPort)

    candidate_repository.summary.return_value = {"total": 0, "byStatus": {}, "byType": {}}
    vocabulary_repository.summary.return_value = {
        "total": 0,
        "approved": 0,
        "activeApproved": 0,
        "byType": {},
    }
    memory_repository.summary.return_value = {
        "total": 0,
        "active": 0,
        "forgotten": 0,
        "byStatus": {},
        "byType": {},
    }
    evaluation_repository.summary.return_value = {
        "total": 0,
        "active": 0,
        "disabled": 0,
        "failing": 0,
        "passing": 0,
        "neverRun": 0,
        "byCategory": {},
    }
    fine_tuning_repository.summary.return_value = {
        "samplesTotal": 0,
        "samplesCaptured": 0,
        "samplesApproved": 0,
        "samplesRejected": 0,
        "datasetsApproved": 0,
        "activeDeploys": 0,
    }
    knowledge_repository.count_active_documents_by_source_type.return_value = {}
    vocabulary_repository.list_top_typo_rules.return_value = []

    summary = GetAdminLearningSummaryUseCase(
        candidate_repository=candidate_repository,
        vocabulary_repository=vocabulary_repository,
        memory_repository=memory_repository,
        evaluation_repository=evaluation_repository,
        fine_tuning_repository=fine_tuning_repository,
        knowledge_repository=knowledge_repository,
    ).execute(hours=24)

    candidate_repository.summary.assert_called_once()
    knowledge_repository.count_active_documents_by_source_type.assert_called_once()
    assert "windowHours" in summary


def test_knowledge_candidate_service_uses_injected_port():
    repository = Mock(spec=LearningCandidateRepositoryPort)
    vocabulary_repository = Mock(spec=VocabularyTermRepositoryPort)
    repository.list_candidates.return_value = ([], 0)

    service = ChatKnowledgeCandidateService(
        candidate_repository=repository,
        vocabulary_repository=vocabulary_repository,
    )
    result = service.list_candidates(limit=5, offset=0)

    repository.list_candidates.assert_called_once()
    assert result["pagination"]["total"] == 0


def test_document_vision_list_attachments_uses_port(monkeypatch):
    repository = Mock(spec=ChatAttachmentRepositoryPort)
    repository.list_attachments_by_ids.return_value = []

    monkeypatch.setattr(
        "app.application.services.chat_document_vision_service._default_attachment_repository",
        lambda: repository,
    )

    items = ChatDocumentVisionService._list_attachments(
        user_id="00000000-0000-0000-0000-000000000001",
        session_id="00000000-0000-0000-0000-000000000002",
        attachment_ids=["00000000-0000-0000-0000-000000000003"],
    )

    repository.list_attachments_by_ids.assert_called_once()
    assert items == []
