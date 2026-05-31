"""Contexto adicional no prompt para turnos de correção textual."""

from __future__ import annotations

from app.domain.services.chat_text_correction_intent_service import (
    ChatTextCorrectionIntentService,
)


class ChatTextCorrectionPromptSupplementService:
    @classmethod
    def build(
        cls,
        *,
        message: str | None,
        text_correction_subtype: str | None = None,
    ) -> str:
        ctx = ChatTextCorrectionIntentService.extract_context(message)
        subtype = text_correction_subtype or ctx.get("subtype") or "text_correct_basic"

        lines = [
            "Instruções adicionais — correção de texto:",
            f"- Subtipo detectado: {subtype}.",
            "- Não consulte ERP, SQL, RAG nem actions neste turno.",
            "- Preserve códigos, nomes próprios, siglas, datas e valores do original.",
        ]

        source = ctx.get("sourceText")

        if source:
            preview = source if len(source) <= 600 else f"{source[:600]}…"
            lines.append(f"- Texto a corrigir (extraído do pedido): «{preview}»")

        if ctx.get("preserveStyle"):
            lines.append(
                "- Modo: preservar estilo — corrija ortografia/concordância/pontuação apenas."
            )

        if ctx.get("deliverFinalOnly"):
            lines.append("- Modo: entregar **somente** a versão final, sem explicação.")

        if ctx.get("explainChanges") or subtype == "text_correct_explain":
            lines.append(
                "- Modo: explicar — use «Versão corrigida» e «Ajustes realizados» (lista curta)."
            )

        if subtype == "text_correct_compare":
            lines.append("- Modo: antes/depois — seções Antes, Depois e O que mudou.")

        if subtype == "text_correct_formal":
            lines.append("- Tom: mais formal e corporativo, sem exagero.")

        if subtype == "text_correct_professional":
            lines.append("- Tom: profissional, claro e respeitoso.")

        if subtype == "text_correct_simple":
            lines.append("- Tom: linguagem simples e direta.")

        if subtype == "text_correct_clear":
            lines.append("- Objetivo: melhorar clareza mantendo o sentido.")

        if subtype == "text_review_quality":
            lines.append(
                "- Avalie se o texto está adequado; se necessário, sugira versão corrigida."
            )

        codes = ctx.get("preservedCodes") or []

        if codes:
            lines.append(f"- Códigos/valores a preservar na resposta: {', '.join(codes)}.")

        if ctx.get("tone"):
            lines.append(f"- Tom pedido: {ctx['tone']}.")

        return "\n".join(lines)
