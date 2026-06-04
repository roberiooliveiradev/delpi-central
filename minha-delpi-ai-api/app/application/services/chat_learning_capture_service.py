from app.application.services.chat_knowledge_candidate_service import (
    ChatKnowledgeCandidateService,
)
from app.domain.services.chat_vocabulary_learning_service import (
    ChatVocabularyLearningService,
)
from app.infrastructure.config.settings import Settings

# Motivos de feedback negativo que indicam falha de entendimento/normalização.
_UNDERSTANDING_REASONS = frozenset(
    {
        "did_not_understand",
        "nao_entendeu",
        "wrong_intent",
        "off_topic",
        "incomplete",
    }
)


class ChatLearningCaptureService:
    """Captura candidatos de aprendizado a partir de sinais reais (playbook §16, §31).

    Fase 1: ancorada no feedback negativo (caminho transacional, fora do hot path).
    Detecta definição explícita ou registra a pergunta como candidato de normalização.
    """

    def __init__(
        self,
        candidate_service: ChatKnowledgeCandidateService | None = None,
    ):
        self.candidate_service = candidate_service or ChatKnowledgeCandidateService()

    def capture_from_negative_feedback(
        self,
        *,
        user_question: str | None,
        reason: str | None = None,
        project_id: str | None = None,
        created_by: str | None = None,
    ) -> dict | None:
        if not Settings.CHAT_LEARNING_ENABLED or not Settings.CHAT_LEARNING_CAPTURE_FROM_FEEDBACK:
            return None

        question = str(user_question or "").strip()

        if not question:
            return None

        candidate = ChatVocabularyLearningService.detect_explicit_definition(question)

        if candidate is None:
            # Sinal mais forte quando o motivo indica falha de entendimento.
            base_confidence = 0.5 if (reason in _UNDERSTANDING_REASONS) else 0.35
            candidate = ChatVocabularyLearningService.build_normalization_candidate(
                question,
                source="feedback",
                base_confidence=base_confidence,
            )

        if candidate is None:
            return None

        if project_id and candidate.get("scope") == "project":
            candidate["projectId"] = project_id

        return self.candidate_service.register_candidate(candidate, created_by=created_by)
