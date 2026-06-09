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
        "analisar desenho tecnico",
        "analisar desenho técnico",
        "analise o desenho",
        "análise o desenho",
        "analise desenho tecnico",
        "análise desenho técnico",
        "analise este desenho",
        "análise este desenho",
        "analise tecnica do desenho",
        "análise técnica do desenho",
        "analise do pdf do desenho",
        "análise do pdf do desenho",
        "reanalisar desenho",
        "reanálise do desenho",
        "validar pdf",
        "validar o pdf",
        "validar pdf do desenho",
        "validar o pdf do desenho",
        "revisar pdf do desenho",
        "revisar o pdf do desenho",
        "validar desenho",
        "validar o desenho",
        "validar desenho tecnico",
        "validar desenho técnico",
        "conferir desenho",
        "conferir o desenho",
        "conferir desenho tecnico",
        "conferir desenho técnico",
        "revisar desenho",
        "revisar o desenho",
        "revisar desenho tecnico",
        "revisar desenho técnico",
        "auditar desenho",
        "auditoria do desenho",
        "validar bom",
        "conferir bom",
        "validar cotas",
        "conferir cotas",
        "conferir decape",
        "conferir decapes",
        "validar codigo intermediario",
        "validar código intermediário",
        "validar carimbo",
        "conferir carimbo",
        "validar cabecalho do desenho",
        "validar cabeçalho do desenho",
        "validar tabela de materiais",
        "conferir tabela de materiais",
        "validar roteiro do desenho",
        "validar inspecao do desenho",
        "validar inspeção do desenho",
        "verificar desenho antes",
        "liberar este desenho",
        "liberar o desenho",
        "liberar desenho para producao",
        "liberar desenho para produção",
        "aprovar desenho",
        "reprovar desenho",
        "relatorio tecnico do desenho",
        "relatório técnico do desenho",
        "gerar relatorio tecnico",
        "gerar relatório técnico",
        "gerar relatorio delpi",
        "gerar relatório delpi",
        "emitir relatorio tecnico",
        "emitir relatório técnico",
        "montar relatorio tecnico",
        "montar relatório técnico",
        "relatorio de conformidade",
        "relatório de conformidade",
        "relatorio de conformidade delpi",
        "relatório de conformidade delpi",
        "gerar relatorio de conformidade",
        "gerar relatório de conformidade",
        "emitir relatorio de conformidade",
        "emitir relatório de conformidade",
        "conformidade delpi",
        "validar conformidade delpi",
        "validar conformidade do desenho",
        "checklist de conformidade",
        "validacao do desenho",
        "validação do desenho",
        "conferir desenho com protheus",
        "conferir com o protheus",
        "validar com protheus",
        "comparar pdf com protheus",
        "comparar desenho com api",
        "comparar desenho com a api",
        "analise de desenho",
        "análise de desenho",
        "analise delpi",
        "análise delpi",
    )

    _DRAWING_VOCABULARY = (
        "desenho",
        "desenho tecnico",
        "desenho técnico",
        "folha de desenho",
        "lamina do desenho",
        "lâmina do desenho",
        "folha tecnica",
        "folha técnica",
        "revisao do desenho",
        "revisão do desenho",
        "carimbo",
        "titulo do desenho",
        "título do desenho",
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
        "roteiro do desenho",
        "inspecao dimensional",
        "inspeção dimensional",
        "nao conformidade",
        "não conformidade",
        "conformidade",
        "validar cabecalho",
        "validar cabeçalho",
        "checklist do desenho",
        "checklist de desenho",
    )

    _PDF_ATTACHMENT_PHRASES = (
        "desenho em pdf",
        "pdf do desenho",
        "pdf tecnico",
        "pdf técnico",
        "pdf anexado",
        "pdf anexo",
        "este pdf",
        "esse pdf",
        "arquivo anexado do desenho",
        "anexo do desenho",
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

        if any(phrase in normalized for phrase in cls._PDF_ATTACHMENT_PHRASES):
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

        if any(
            term in normalized
            for term in (
                "validar cotas",
                "conferir decape",
                "conferir cotas",
                "validar bom",
                "conferir bom",
                "validar cabecalho",
                "validar cabeçalho",
                "validar carimbo",
                "carimbo",
                "liberar",
                "relatorio tecnico",
                "relatório técnico",
                "relatorio de conformidade",
                "relatório de conformidade",
                "conformidade delpi",
                "checklist de conformidade",
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
