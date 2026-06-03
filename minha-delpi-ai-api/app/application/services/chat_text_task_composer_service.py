"""Composição de texto (e-mail, mensagens) a partir de dados operacionais já consultados."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService


class ChatTextTaskComposerService:
    @classmethod
    def build_supplement_for_mixed_turn(
        cls,
        *,
        message: str,
        tool_calls: list | None,
    ) -> str | None:
        """Após consulta operacional no mesmo turno, redige e-mail/mensagem pedida."""
        category = ChatTextTaskIntentService.classify(message)

        if category not in {"email", "write", "message", "document"}:
            return None

        if not ChatTextTaskIntentService.is_mixed_text_and_operational(message):
            return None

        summary = cls._latest_tool_summary(tool_calls)

        if not summary:
            return None

        draft = cls.build_operational_email_draft(summary, message)

        return draft.get("text") if draft else None

    @classmethod
    def build_operational_email_draft(
        cls,
        summary: dict,
        message: str,
    ) -> dict | None:
        from app.application.services.chat_email_operational_composer_service import (
            ChatEmailOperationalComposerService,
        )

        return ChatEmailOperationalComposerService.build_from_summary(summary, message)

    @classmethod
    def build_email_from_conversation(
        cls,
        message: str,
        previous_messages: list[Any] | None,
    ) -> str | None:
        """Follow-up: e-mail com base na tabela/dados da consulta anterior."""
        from app.application.services.chat_data_interpretation_answer_service import (
            ChatDataInterpretationAnswerService,
        )
        from app.domain.services.chat_analysis_intent_service import (
            ChatAnalysisIntentService,
        )

        if not ChatAnalysisIntentService.is_email_from_operational_data_request(
            message,
            previous_messages,
        ):
            return None

        summaries = ChatDataInterpretationAnswerService._collect_summaries(previous_messages)

        if not summaries:
            return None

        draft = cls.build_operational_email_draft(summaries[-1], message)

        return draft.get("text") if draft else None

    @classmethod
    def build_operational_email_with_metadata(
        cls,
        *,
        message: str,
        tool_calls: list | None = None,
        previous_messages: list[Any] | None = None,
    ) -> dict | None:
        """Rascunho operacional + metadata para chips/validação (turno misto ou follow-up)."""
        summary = None

        if tool_calls:
            summary = cls._latest_tool_summary(tool_calls)

        if not summary and previous_messages:
            from app.application.services.chat_data_interpretation_answer_service import (
                ChatDataInterpretationAnswerService,
            )

            summaries = ChatDataInterpretationAnswerService._collect_summaries(previous_messages)

            if summaries:
                summary = summaries[-1]

        if not summary:
            return None

        return cls.build_operational_email_draft(summary, message)

    @classmethod
    def attachment_text_task_instruction(cls, *, attachment_context: str | None) -> str:
        if not str(attachment_context or "").strip():
            return (
                "Tarefa textual: corrija ou reescreva o trecho indicado na mensagem do usuário. "
                "Entregue só o texto final corrigido, sem dizer que não tem acesso a documentos."
            )

        return (
            "Tarefa textual com anexo: use o conteúdo dos arquivos anexados nesta mensagem "
            "(seção de anexos abaixo) como fonte principal. "
            "Não diga que não tem acesso ao documento quando o trecho estiver no contexto. "
            "Pode resumir, corrigir, revisar, traduzir, extrair pendências ou transformar em "
            "ata, checklist, relatório, comunicado ou e-mail conforme o pedido. "
            "Entregue a versão solicitada; use placeholders para dados ausentes."
        )

    @classmethod
    def _latest_tool_summary(cls, tool_calls: list | None) -> dict | None:
        from app.application.services.chat_data_interpretation_answer_service import (
            ChatDataInterpretationAnswerService,
        )

        for tool_call in reversed(tool_calls or []):
            if not isinstance(tool_call, dict):
                continue

            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            summary = ChatDataInterpretationAnswerService._resolve_tool_summary(metadata)

            if summary:
                return summary

        return None

