"""Intent de análise de desenhos técnicos DELPI (PDF × API × normas) — Onda 12."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import (
    ChatAssistantContentService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)

DRAWING_ANALYSIS_SKILL_KEY = "drawing-analysis-delpi"
DRAWING_ANALYSIS_SKILL_ALIAS = "drawing-analyser"
_INTENT_CONTENT_BUNDLE = "drawing_query_intent"


class ChatDrawingIntentService:
    """Detecta pedidos de validação de desenho técnico em PDF contra Protheus."""

    @classmethod
    def _terms(cls, *path: str) -> tuple[str, ...]:
        return tuple(
            ChatAssistantContentService.list(_INTENT_CONTENT_BUNDLE, *path)
        )

    @classmethod
    def _direct_answer(cls, key: str, *, default: str = "") -> str:
        return ChatAssistantContentService.get(
            _INTENT_CONTENT_BUNDLE,
            "directAnswers",
            key,
            default=default,
        )

    @classmethod
    def normalize_skill_key(cls, skill_key: str | None) -> str:
        normalized = str(skill_key or "").strip().lower()

        if normalized == DRAWING_ANALYSIS_SKILL_ALIAS:
            return DRAWING_ANALYSIS_SKILL_KEY

        return normalized

    @classmethod
    def is_drawing_analysis_request(
        cls,
        message: str | None,
        *,
        attachment_ids: list[str] | None = None,
    ) -> bool:
        from app.domain.services.chat_drawing_report_adjustment_intent_service import (
            ChatDrawingReportAdjustmentIntentService,
        )

        if ChatDrawingReportAdjustmentIntentService.has_adjustment_signal(message):
            return False

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if any(trigger in normalized for trigger in cls._terms("explicitTriggers")):
            return True

        if attachment_ids and any(
            term in normalized for term in cls._terms("attachmentVocabulary")
        ):
            return True

        if any(phrase in normalized for phrase in cls._terms("pdfAttachmentPhrases")):
            return True

        return False

    @classmethod
    def blocks_presentation_only_shortcut(cls, message: str | None) -> bool:
        """Turnos de relatório de desenho exibem markdown completo — não título da UI rica."""
        return cls.is_drawing_analysis_request(message)

    @classmethod
    def wants_product_analyser(cls, message: str | None) -> bool:
        if not cls.is_drawing_analysis_request(message):
            return False

        return bool(cls.resolve_product_code(message))

    @classmethod
    def resolve_product_code(cls, message: str | None) -> str | None:
        return ChatProductQueryIntentService.extract_product_code(message)

    @classmethod
    def requires_pdf_for_full_analysis(
        cls,
        message: str | None,
        *,
        attachment_ids: list[str] | None,
    ) -> bool:
        if attachment_ids:
            return False

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if any(term in normalized for term in cls._terms("requiresPdfTerms")):
            return True

        return cls.is_drawing_analysis_request(message, attachment_ids=attachment_ids)

    @classmethod
    def build_skill_disabled_answer(cls) -> str:
        return cls._direct_answer("skillDisabled")

    @classmethod
    def build_missing_pdf_answer(cls) -> str:
        return cls._direct_answer("missingPdf")

    @classmethod
    def build_missing_product_code_answer(cls) -> str:
        return cls._direct_answer("missingProductCode")

    @classmethod
    def build_drawing_library_not_found_answer(cls, product_code: str | None = None) -> str:
        template = cls._direct_answer(
            "drawingLibraryNotFound",
            default=(
                "Não encontrei o PDF do desenho na biblioteca corporativa"
                + (f" para o produto {product_code}." if product_code else ".")
                + " Anexe o PDF ou confira o código informado."
            ),
        )
        code = str(product_code or "").strip()

        if code and "{code}" in template:
            return template.replace("{code}", code)

        return template

    @classmethod
    def build_memory_limited_answer(cls) -> str:
        return cls._direct_answer(
            "memoryLimited",
            default=(
                "Não consegui concluir a leitura avançada do PDF por falta de memória "
                "no servidor. Tente novamente em instantes ou aumente a memória do ambiente."
            ),
        )

    @classmethod
    def build_llm_fallback_policy_addon(
        cls,
        message: str | None,
        *,
        attachment_ids: list[str] | None = None,
    ) -> str:
        if not cls.is_drawing_analysis_request(message, attachment_ids=attachment_ids):
            return ""

        policy_file = ChatAssistantContentService.get(
            _INTENT_CONTENT_BUNDLE,
            "llmFallback",
            "policyFile",
            default="drawing-report-llm-fallback.md",
        )
        title = ChatAssistantContentService.get(
            _INTENT_CONTENT_BUNDLE,
            "llmFallback",
            "title",
            default="Relatório de Análise de Desenho DELPI",
        )

        from app.domain.services.prompt_policy_service import PromptPolicyService

        policy_body = PromptPolicyService()._load_policy(policy_file)

        if not policy_body:
            return ""

        return f"\n\n{policy_body}".strip()

    @classmethod
    def build_rag_query(cls, message: str | None) -> str:
        base = str(message or "").strip()
        suffix = ChatAssistantContentService.get(
            _INTENT_CONTENT_BUNDLE,
            "ragQuery",
            "drawingAnalysisSuffix",
            default="",
        )

        if not suffix:
            return base

        if not base:
            return suffix

        return f"{base} {suffix}".strip()
