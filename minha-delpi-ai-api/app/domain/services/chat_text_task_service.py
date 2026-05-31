"""Orquestração de tarefas textuais — Playbook 03 (chat base)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService


class ChatTextTaskService:
    """Facade textual: classificação, contexto, metadata e supplements."""

    _CATEGORY_TO_TYPE: dict[str, str] = {
        "correct": "correction",
        "rewrite": "rewrite",
        "translate": "translation",
        "summarize": "summary",
        "structure": "structure",
        "email": "email",
        "message": "message",
        "write": "compose",
        "tone_adjust": "tone",
        "extract_actions": "extract_actions",
        "document": "document",
        "minutes": "minutes",
        "announcement": "announcement",
        "compare": "comparison",
        "organize": "organize",
        "simplify": "simplify",
    }

    @classmethod
    def is_text_task(cls, message: str | None, *, previous_messages: list | None = None) -> bool:
        return ChatTextTaskIntentService.is_pure_text_task(
            message,
            previous_messages=previous_messages,
        )

    @classmethod
    def classify(cls, message: str | None) -> dict[str, Any]:
        category = ChatTextTaskIntentService.classify(message) or "compose"
        normalized = (message or "").strip().lower()
        subtype = cls._resolve_subtype(category, normalized)
        tone = cls._detect_tone(normalized)
        deliver_final_only = cls._wants_final_only(normalized)
        source = cls._detect_source(normalized)

        return {
            "type": cls._CATEGORY_TO_TYPE.get(category, "compose"),
            "subtype": subtype,
            "category": category,
            "tone": tone,
            "format": cls._detect_format(normalized, subtype),
            "source": source,
            "preserveMeaning": True,
            "deliverFinalOnly": deliver_final_only,
            "containsTechnicalTerms": cls._has_technical_terms(message or ""),
            "preservedCodes": cls._extract_preserved_tokens(message or ""),
        }

    @classmethod
    def build_prompt_supplement(
        cls,
        *,
        message: str | None,
        workspace_context: dict | None = None,
        previous_messages: list | None = None,
        text_correction_mode: bool = False,
        text_correction_subtype: str | None = None,
        email_writing_mode: bool = False,
    ) -> str | None:
        if text_correction_mode:
            from app.application.services.chat_text_correction_prompt_supplement_service import (
                ChatTextCorrectionPromptSupplementService,
            )

            block = ChatTextCorrectionPromptSupplementService.build(
                message=message,
                text_correction_subtype=text_correction_subtype,
                workspace_context=workspace_context,
                previous_messages=previous_messages,
            )

            return block or None

        if email_writing_mode:
            from app.application.services.chat_email_prompt_supplement_service import (
                ChatEmailPromptSupplementService,
            )

            return ChatEmailPromptSupplementService.build(
                message=message,
                workspace_context=workspace_context,
            ) or None

        ctx = cls.classify(message)
        lines = [
            "Modo especialista em textos (Playbook 03):",
            f"- Tipo: {ctx.get('type')} / subtipo: {ctx.get('subtype')}",
            "- Não consulte API, SQL, RAG ou web neste turno.",
            "- Preserve sentido, códigos, nomes, valores e siglas.",
        ]

        if ctx.get("deliverFinalOnly"):
            lines.append("- Entregue só a versão final, sem explicação longa.")

        if ctx.get("tone"):
            lines.append(f"- Tom desejado: {ctx['tone']}.")

        template = cls._template_hint(ctx.get("subtype"))

        if template:
            lines.append(template)

        from app.domain.services.chat_text_task_preference_service import (
            ChatTextTaskPreferenceService,
        )

        pref_block = ChatTextTaskPreferenceService.format_prompt_block(workspace_context)

        if pref_block:
            lines.append(pref_block)

        return "\n".join(lines)

    @classmethod
    def build_text_task_metadata(
        cls,
        *,
        message: str | None,
        answer: str | None = None,
        workspace_context: dict | None = None,
    ) -> dict[str, Any] | None:
        from app.domain.services.chat_text_correction_intent_service import (
            ChatTextCorrectionIntentService,
        )
        from app.domain.services.chat_email_intent_service import ChatEmailIntentService

        if ChatTextCorrectionIntentService.is_text_correction(message):
            payload = ChatTextCorrectionIntentService.build_text_task_metadata(
                message=message,
                answer=answer,
            )

            if payload:
                return payload

        if ChatEmailIntentService.is_email_writing(message) or (workspace_context or {}).get(
            "emailWritingMode"
        ):
            payload = ChatEmailIntentService.build_text_task_metadata(
                message=message,
                answer=answer,
            )

            if payload:
                return payload

        if not cls.is_text_task(message):
            if not (workspace_context or {}).get("textTaskMode"):
                return None

        ctx = cls.classify(message)
        ctx["suggestions"] = cls.default_suggestions(ctx.get("subtype"))

        return {"textTask": ctx}

    @classmethod
    def default_suggestions(cls, subtype: str | None) -> list[str]:
        base = [
            "Deixar mais formal",
            "Deixar mais curto",
            "Deixar mais direto",
            "Deixar mais cordial",
            "Colocar na lousa",
            "Copiar texto",
        ]

        if subtype in {"text_correct", "text_rewrite"}:
            base.insert(3, "Mostrar alterações")

        if subtype not in {"text_email_create", "text_email_reply"}:
            base.append("Criar e-mail")

        if subtype == "text_summarize":
            base.append("Resumo executivo")

        if subtype == "text_translate":
            base.append("Traduzir")

        return cls._dedupe(base)[:8]

    @staticmethod
    def _resolve_subtype(category: str, normalized: str) -> str:
        if category == "correct":
            if "mostre" in normalized and "alter" in normalized:
                return "text_review_quality"

            return "text_correct"

        if category == "rewrite":
            if "formal" in normalized:
                return "text_formalize"

            if "simples" in normalized or "simplif" in normalized:
                return "text_simplify"

            if "profissional" in normalized:
                return "text_professionalize"

            return "text_rewrite"

        if category == "translate":
            return "text_translate"

        if category == "summarize":
            if "executivo" in normalized:
                return "text_summarize_executive"

            if "pend" in normalized or "decis" in normalized:
                return "text_extract_actions"

            return "text_summarize"

        if category == "email":
            if "responda" in normalized or "resposta" in normalized:
                return "text_email_reply"

            return "text_email_create"

        if category == "minutes":
            return "text_minutes"

        if category == "announcement":
            return "text_announcement"

        if category == "compare":
            return "text_compare"

        if category == "organize":
            return "text_organize"

        if category == "simplify":
            return "text_simplify"

        if category == "structure":
            if "checklist" in normalized or "lista de tarefas" in normalized:
                return "text_checklist"

            if "ata" in normalized or "reuni" in normalized:
                return "text_minutes"

            return "text_organize"

        if category == "document":
            return "text_announcement"

        if category == "extract_actions":
            return "text_extract_actions"

        if category == "tone_adjust":
            return "text_tone_adjust"

        if "compare" in normalized or "compar" in normalized:
            return "text_compare"

        if "explique de forma simples" in normalized or "simplif" in normalized:
            return "text_simplify"

        return "text_compose"

    @staticmethod
    def _template_hint(subtype: str | None) -> str | None:
        hints = {
            "text_correct": "- Resposta: «Segue a versão corrigida:» + texto.",
            "text_email_create": "- Inclua Assunto: e corpo; não invente assinatura.",
            "text_email_reply": "- Resposta a e-mail; preserve contexto do original.",
            "text_announcement": "- Use título # Comunicado e tom objetivo.",
            "text_minutes": "- Estrutura de ata: data, participantes, decisões, pendências.",
            "text_checklist": "- Lista com - [ ] e verbos de ação.",
            "text_summarize": "- Resumo fiel; não invente fatos.",
            "text_compare": "- Tabela comparativa + melhor opção.",
        }

        return hints.get(subtype or "")

    @staticmethod
    def _detect_tone(normalized: str) -> str | None:
        if "formal" in normalized:
            return "formal"

        if "cordial" in normalized or "educad" in normalized:
            return "cordial"

        if "direto" in normalized or "objetiv" in normalized:
            return "direct"

        if "simples" in normalized:
            return "simple"

        if "profissional" in normalized:
            return "professional"

        return None

    @staticmethod
    def _detect_format(normalized: str, subtype: str | None) -> str:
        if subtype in {"text_checklist", "text_minutes", "text_announcement"}:
            return "markdown"

        if "tabela" in normalized:
            return "table"

        return "plain"

    @staticmethod
    def _detect_source(normalized: str) -> str:
        if "lousa" in normalized or "canvas" in normalized:
            return "canvas"

        if "anexo" in normalized or "arquivo" in normalized or "pdf" in normalized:
            return "attachment"

        return "user_message"

    @staticmethod
    def _wants_final_only(normalized: str) -> bool:
        return any(
            phrase in normalized
            for phrase in (
                "so a versao final",
                "só a versão final",
                "so corrija",
                "só corrija",
                "sem explicar",
                "nao explique",
                "não explique",
                "apenas corrija",
            )
        )

    @staticmethod
    def _has_technical_terms(text: str) -> bool:
        return bool(re.search(r"\b(BOM|OV|LMP|Protheus|\d{5,})\b", text, re.IGNORECASE))

    @staticmethod
    def _extract_preserved_tokens(text: str) -> list[str]:
        tokens: list[str] = []
        seen: set[str] = set()

        for match in re.finditer(r"\b\d{5,}\b", text):
            value = match.group(0)

            if value not in seen:
                seen.add(value)
                tokens.append(value)

        for term in ("BOM", "OV", "LMP"):
            if re.search(rf"\b{term}\b", text, re.IGNORECASE) and term not in seen:
                seen.add(term)
                tokens.append(term)

        return tokens

    @staticmethod
    def _dedupe(items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []

        for item in items:
            key = item.strip().lower()

            if not key or key in seen:
                continue

            seen.add(key)
            result.append(item)

        return result
