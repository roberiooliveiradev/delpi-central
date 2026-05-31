"""Contexto adicional no prompt para turnos de escrita de e-mail."""

from __future__ import annotations

from app.domain.services.chat_email_intent_service import ChatEmailIntentService
from app.domain.services.chat_email_preference_service import ChatEmailPreferenceService


class ChatEmailPromptSupplementService:
    @classmethod
    def build(
        cls,
        *,
        message: str | None,
        workspace_context: dict | None = None,
        email_subtype: str | None = None,
    ) -> str:
        ctx = ChatEmailIntentService.extract_context(message)
        subtype = email_subtype or ctx.get("subtype") or "email_create"
        working_memory = (workspace_context or {}).get("workingMemory") or {}
        prefs = ChatEmailPreferenceService.detect(message, working_memory=working_memory)

        lines = [
            "Instruções adicionais — e-mail corporativo:",
            f"- Subtipo detectado: {subtype}.",
        ]

        if ctx.get("recipient"):
            lines.append(f"- Destinatário informado: {ctx['recipient']}.")

        if ctx.get("tone"):
            lines.append(f"- Tom pedido: {ctx['tone']}.")

        if ctx.get("audience") == "supplier":
            lines.append("- Público: fornecedor — objetivo e cordial.")
        elif ctx.get("audience") == "customer":
            lines.append("- Público: cliente — cuidado e clareza, sem atribuir culpa.")
        elif ctx.get("audience") == "internal":
            lines.append("- Público: interno — respeitoso e direto.")

        if ctx.get("senderSignature"):
            lines.append(f"- Assinatura informada pelo usuário: {ctx['senderSignature']}.")
        else:
            lines.append("- Assinatura: use [Seu nome]; não invente nome nem cargo.")

        if ctx.get("subjectHint"):
            lines.append(f"- Tema/assunto sugerido pelo usuário: {ctx['subjectHint']}.")

        if "senderName" in (ctx.get("missingFields") or []):
            lines.append("- Campo ausente: nome do remetente → placeholder [Seu nome].")

        if cls._mentions_delpi_ia(message):
            lines.append(
                "- Tema Minha DELPI / IA: cite capacidades reais (agentes, consultas, "
                "textos, anexos, gráficos, lousa, pesquisa web, desenhos, relatórios, "
                "dados internos) sem prometer o que não foi pedido."
            )

        pref_block = ChatEmailPreferenceService.format_prompt_block(prefs)

        if pref_block:
            lines.append(pref_block)

        if subtype in {"email_shorten", "email_formalize", "email_soften", "email_firm"}:
            lines.append(
                "- Refinamento: reescreva o rascunho anterior mantendo fatos; "
                "não invente dados novos."
            )

        if subtype == "email_subjects":
            lines.append("- Entregue 3 opções de assunto numeradas, sem corpo longo.")

        if subtype == "email_translate":
            lines.append("- Traduza mantendo tom corporativo no idioma de destino.")

        return "\n".join(lines)

    @classmethod
    def _mentions_delpi_ia(cls, message: str | None) -> bool:
        lowered = (message or "").lower()

        return any(
            token in lowered
            for token in (
                "minha delpi",
                "inteligência artificial",
                "inteligencia artificial",
                " ia ",
                "chat ia",
            )
        )
