"""Contexto adicional no prompt para turnos de correção textual."""

from __future__ import annotations

from app.domain.services.chat_text_correction_intent_service import (
    ChatTextCorrectionIntentService,
)
from app.domain.services.chat_text_correction_preference_service import (
    ChatTextCorrectionPreferenceService,
)


class ChatTextCorrectionPromptSupplementService:
    @classmethod
    def build(
        cls,
        *,
        message: str | None,
        text_correction_subtype: str | None = None,
        workspace_context: dict | None = None,
    ) -> str:
        working_memory = (workspace_context or {}).get("workingMemory") or {}
        ctx = ChatTextCorrectionIntentService.extract_context(
            message,
            working_memory=working_memory,
        )
        prefs = ChatTextCorrectionPreferenceService.detect(
            message,
            working_memory=working_memory,
        )
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

        source = ctx.get("source")

        if source == "canvas":
            lines.append(
                "- Fonte: texto da lousa/canvas — use o conteúdo atual da lousa como base."
            )
        elif source == "attachment":
            lines.append(
                "- Fonte: anexo/documento — corrija o texto extraído do arquivo enviado."
            )

        codes = ctx.get("preservedCodes") or []

        if codes:
            lines.append(f"- Códigos/valores a preservar na resposta: {', '.join(codes)}.")

        if ctx.get("tone"):
            lines.append(f"- Tom pedido: {ctx['tone']}.")

        pref_block = ChatTextCorrectionPreferenceService.format_prompt_block(prefs)

        if pref_block:
            lines.append(pref_block)

        return "\n".join(lines)
