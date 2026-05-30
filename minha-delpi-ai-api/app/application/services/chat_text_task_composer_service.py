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

        return cls._format_email_from_summary(summary, message)

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

        return cls._format_email_from_summary(summaries[-1], message)

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
            "Entregue a versão corrigida ou redigida solicitada."
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

    @classmethod
    def _format_email_from_summary(cls, summary: dict, message: str) -> str:
        title = str(summary.get("titulo") or "Consulta operacional").strip()
        lines = [
            str(line).strip()
            for line in (summary.get("linhas") or [])
            if str(line or "").strip()
        ][:10]
        product_code = cls._extract_product_code(summary, lines, message)
        subject = cls._infer_subject(title, product_code, message)

        body_lines = [
            "Prezados(as),",
            "",
            f"Segue resumo de **{title.lower()}**" + (f" do produto **{product_code}**" if product_code else "") + ":",
            "",
        ]

        if lines:
            body_lines.extend(f"- {line}" for line in lines)
        else:
            body_lines.append("- Consulta realizada na plataforma; detalhes na tabela da conversa.")

        body_lines.extend(
            [
                "",
                "Fico à disposição para complementar ou detalhar por filial, se necessário.",
                "",
                "Atenciosamente,",
            ]
        )

        return "\n".join(
            [
                f"**Assunto sugerido:** {subject}",
                "",
                "\n".join(body_lines),
            ]
        )

    @classmethod
    def _infer_subject(cls, title: str, product_code: str | None, message: str) -> str:
        lowered = (message or "").lower()

        if "compras" in lowered:
            return f"Alerta — {title}" + (f" — produto {product_code}" if product_code else "")

        if "fornecedor" in lowered:
            return f"Comunicado ao fornecedor — {title}" + (f" — {product_code}" if product_code else "")

        return f"{title}" + (f" — produto {product_code}" if product_code else "")

    @classmethod
    def _extract_product_code(
        cls,
        summary: dict,
        lines: list[str],
        message: str,
    ) -> str | None:
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        code = ChatProductQueryIntentService.extract_product_code(message)

        if code:
            return code

        path = str(summary.get("path") or "")
        match = re.search(r"/products/(\d{5,9})", path)

        if match:
            return match.group(1)

        blob = " ".join(lines)
        match = re.search(r"\b(\d{5,9})\b", blob)

        return match.group(1) if match else None
