"""Aviso user-facing quando a visualização pedida não materializa (dados insuficientes).

Espelha o padrão de ``policyNotice``: a API decide o texto (content JSON) e anexa
ao ``presentationDecision`` / prosa; o MFE apenas renderiza.
"""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)


class PresentationUnmetIntentNoticeService:
    @classmethod
    def resolve_token(cls, metadata: dict[str, Any] | None) -> str | None:
        if not isinstance(metadata, dict):
            return None

        decision = metadata.get("presentationDecision")
        if isinstance(decision, dict):
            token = str(decision.get("unmetIntent") or "").strip()
            if token:
                return token

        intel = metadata.get("presentationIntelligence")
        if isinstance(intel, dict):
            token = str(intel.get("unmetIntent") or "").strip()
            if token:
                return token

        return None

    @classmethod
    def notice_for_token(cls, token: str | None) -> str | None:
        text = ChatPresentationVocabularyService.unmet_intent_notice(
            token,
            default="",
        ).strip()
        return text or None

    @classmethod
    def notice_from_metadata(cls, metadata: dict[str, Any] | None) -> str | None:
        if not isinstance(metadata, dict):
            return None

        decision = metadata.get("presentationDecision")
        if isinstance(decision, dict):
            existing = str(decision.get("unmetIntentNotice") or "").strip()
            if existing:
                return existing

        return cls.notice_for_token(cls.resolve_token(metadata))

    @classmethod
    def apply(
        cls,
        metadata: dict[str, Any] | None,
        *,
        unmet_intent: str | None = None,
    ) -> str | None:
        if not isinstance(metadata, dict):
            return None

        token = str(unmet_intent or "").strip() or cls.resolve_token(metadata)
        if not token:
            return None

        notice = cls.notice_for_token(token)
        if not notice:
            return None

        decision = metadata.get("presentationDecision")
        if not isinstance(decision, dict):
            decision = {}
            metadata["presentationDecision"] = decision

        decision["unmetIntent"] = token
        decision["unmetIntentNotice"] = notice

        # Reusa o slot de notice já tipado no contrato MFE (cap de categorias etc.).
        if not str(decision.get("policyNotice") or "").strip():
            decision["policyNotice"] = notice

        if not metadata.get("llmProseDecoupled") and not metadata.get("dataOnlyPresentation"):
            insight = str(decision.get("insight") or "").strip()
            if notice not in insight:
                decision["insight"] = f"{notice} {insight}".strip() if insight else notice

        cls._prepend_text_presentation(metadata, notice)
        cls._prepend_data_answer_summary(metadata, notice)
        cls._append_attention(metadata, notice)
        cls._prefix_chart_explanation(decision, notice)

        return notice

    @classmethod
    def prepend_to_answer(cls, answer: str | None, notice: str | None) -> str | None:
        body = str(answer or "").strip()
        text = str(notice or "").strip()
        if not text:
            return answer
        if not body:
            return text
        if text in body:
            return body
        return f"{text}\n\n{body}"

    @classmethod
    def collect_from_tool_calls(cls, tool_calls: list | None) -> str | None:
        if not isinstance(tool_calls, list):
            return None

        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue
            metadata = tool_call.get("metadata")
            notice = cls.notice_from_metadata(metadata if isinstance(metadata, dict) else None)
            if notice:
                return notice

        return None

    @classmethod
    def _prepend_text_presentation(cls, metadata: dict[str, Any], notice: str) -> None:
        text_presentation = metadata.get("textPresentation")
        if not isinstance(text_presentation, dict):
            return

        markdown = str(text_presentation.get("markdown") or "").strip()
        if not markdown:
            text_presentation["markdown"] = notice
            return
        if notice in markdown:
            return
        text_presentation["markdown"] = f"{notice}\n\n{markdown}"

    @classmethod
    def _prepend_data_answer_summary(cls, metadata: dict[str, Any], notice: str) -> None:
        data_answer = metadata.get("dataAnswer")
        if not isinstance(data_answer, dict):
            return

        summary = data_answer.get("summary")
        if not isinstance(summary, dict):
            return

        answer = str(summary.get("answer") or "").strip()
        if not answer:
            summary["answer"] = notice
            return
        if notice in answer:
            return
        summary["answer"] = f"{notice}\n\n{answer}"

    @classmethod
    def _append_attention(cls, metadata: dict[str, Any], notice: str) -> None:
        commentary = metadata.get("dataCommentary")
        if not isinstance(commentary, dict):
            commentary = {}
            metadata["dataCommentary"] = commentary

        attention = commentary.get("attention")
        if not isinstance(attention, list):
            attention = []
            commentary["attention"] = attention

        if notice not in attention:
            attention.insert(0, notice)

    @classmethod
    def _prefix_chart_explanation(cls, decision: dict[str, Any], notice: str) -> None:
        explanation = str(decision.get("chartExplanation") or "").strip()
        if not explanation:
            decision["chartExplanation"] = notice
            return
        if notice in explanation:
            return
        decision["chartExplanation"] = f"{notice}\n\n{explanation}"
