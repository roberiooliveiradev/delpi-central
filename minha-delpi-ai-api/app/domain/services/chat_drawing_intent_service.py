"""Intent de análise de desenhos técnicos DELPI (PDF × API × normas) — Onda 12."""

from __future__ import annotations

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)

DRAWING_ANALYSIS_SKILL_KEY = "drawing-analysis-delpi"
DRAWING_ANALYSIS_SKILL_ALIAS = "drawing-analyser"


class ChatDrawingIntentService:
    """Detecta pedidos de validação de desenho técnico em PDF contra Protheus."""

    _EXPLICIT_TRIGGERS = (
        "analisar desenho",
        "analisar o desenho",
        "analise o desenho",
        "análise o desenho",
        "analise este desenho",
        "análise este desenho",
        "validar pdf",
        "validar o pdf",
        "validar desenho",
        "conferir desenho",
        "conferir o desenho",
        "revisar desenho",
        "revisar o desenho",
        "revisar desenho tecnico",
        "revisar desenho técnico",
        "validar bom",
        "validar cotas",
        "conferir decape",
        "conferir decapes",
        "validar codigo intermediario",
        "validar código intermediário",
        "verificar desenho antes",
        "liberar este desenho",
        "liberar o desenho",
        "relatorio tecnico do desenho",
        "relatório técnico do desenho",
        "gerar relatorio tecnico",
        "gerar relatório técnico",
        "conferir desenho com protheus",
        "conferir com o protheus",
        "validar com protheus",
        "analise de desenho",
        "análise de desenho",
        "analise delpi",
        "análise delpi",
    )

    _DRAWING_VOCABULARY = (
        "desenho",
        "desenho tecnico",
        "desenho técnico",
        "revisao do desenho",
        "revisão do desenho",
        "carimbo",
        "tabela de materiais",
        "decape",
        "decapes",
        "intermediario 50",
        "intermediário 50",
        "codigo 50xx",
        "código 50xx",
        "sg1010",
        "qp6",
        "qp7",
        "qp8",
        "validar cabecalho",
        "validar cabeçalho",
        "checklist do desenho",
        "checklist de desenho",
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
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if any(trigger in normalized for trigger in cls._EXPLICIT_TRIGGERS):
            return True

        if attachment_ids and any(term in normalized for term in cls._DRAWING_VOCABULARY):
            return True

        if any(
            phrase in normalized
            for phrase in (
                "desenho em pdf",
                "pdf do desenho",
                "pdf anexado",
                "este pdf",
                "esse pdf",
            )
        ):
            return True

        return False

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

        if any(
            term in normalized
            for term in (
                "validar cotas",
                "conferir decape",
                "validar bom",
                "validar cabecalho",
                "validar cabeçalho",
                "carimbo",
                "liberar",
                "relatorio tecnico",
                "relatório técnico",
            )
        ):
            return True

        return cls.is_drawing_analysis_request(message, attachment_ids=attachment_ids)

    @classmethod
    def build_skill_disabled_answer(cls) -> str:
        return (
            "Para análise de desenhos técnicos DELPI, habilite a skill "
            "**Análise de Desenhos DELPI** (`drawing-analysis-delpi`) no agente desta conversa."
        )

    @classmethod
    def build_missing_pdf_answer(cls) -> str:
        return "Para analisar o desenho, preciso que você anexe o PDF."

    @classmethod
    def build_missing_product_code_answer(cls) -> str:
        return (
            "Informe o código DELPI do produto (ex.: 90260140) ou anexe um PDF com carimbo legível "
            "para eu consultar a API e gerar o relatório técnico."
        )
