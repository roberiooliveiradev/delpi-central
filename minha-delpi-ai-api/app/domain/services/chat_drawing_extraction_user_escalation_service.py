"""Política de escalação ao usuário após OCR — só depois do solve por LLM/VLM.

Ordem canônica:
1. OCR / Tesseract (+ confirmação focal)
2. LLM/VLM solve (quando confiança < limiar)
3. Só então pending / «não consegui ler» para o usuário
"""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "drawing_stamp"


class ChatDrawingExtractionUserEscalationService:
    @classmethod
    def llm_solve_config(cls) -> dict[str, Any]:
        retry = ChatAssistantContentService.get_node(_BUNDLE, "extractionQualityRetry")

        if not isinstance(retry, dict):
            return {}

        node = retry.get("llmSolve")

        return dict(node) if isinstance(node, dict) else {}

    @classmethod
    def llm_solve_enabled(cls) -> bool:
        return bool(cls.llm_solve_config().get("enabled", True))

    @classmethod
    def require_llm_before_user_escalation(cls) -> bool:
        return bool(cls.llm_solve_config().get("requireBeforeUserEscalation", True))

    @classmethod
    def llm_solve_metadata(cls, pdf_extract: dict[str, Any] | None) -> dict[str, Any]:
        payload = pdf_extract if isinstance(pdf_extract, dict) else {}
        retry = payload.get("extractionQualityRetry")

        if isinstance(retry, dict):
            node = retry.get("llmSolve")

            if isinstance(node, dict):
                return dict(node)

        direct = payload.get("llmSolve")

        return dict(direct) if isinstance(direct, dict) else {}

    @classmethod
    def allows_user_escalation(
        cls,
        *,
        pdf_extract: dict[str, Any] | None,
        meets_threshold: bool,
    ) -> bool:
        """Pending / aviso ao usuário só quando a leitura núcleo falhou e o LLM já foi esgotado."""
        if meets_threshold:
            return False

        if not cls.llm_solve_enabled() or not cls.require_llm_before_user_escalation():
            return True

        meta = cls.llm_solve_metadata(pdf_extract)

        if meta.get("resolved") is True:
            return False

        if meta.get("attempted") is True:
            return True

        # Ainda não tentou LLM — não escalar (o solve deve rodar antes da validação).
        if not meta:
            return False

        # Tentativa marcada como skip (ex.: VLM indisponível) → escalar.
        return True

    @classmethod
    def used_llm_solve(cls, pdf_extract: dict[str, Any] | None) -> bool:
        meta = cls.llm_solve_metadata(pdf_extract)

        return bool(meta.get("attempted"))
