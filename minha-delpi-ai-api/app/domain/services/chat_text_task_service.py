"""Orquestração de tarefas textuais — Playbook 03 (chat base)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService


class ChatTextTaskService:
    """Facade textual: classificação, contexto, metadata e supplements."""

    _CATEGORY_TO_TYPE: dict[str, str] = {
        "correct": "correction",
        "review": "review",
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
        "letter": "letter",
        "report": "report",
        "documentation": "documentation",
        "explain": "explanation",
        "eli5": "explanation",
        "action_plan": "action_plan",
        "adapt_audience": "adaptation",
        "to_table": "structure",
        "memorandum": "document",
        "conversation_transform": "structure",
    }

    _SUBTYPE_TO_INTENT: dict[str, str] = {
        "text_correct": "text.correct",
        "text_review_quality": "text.review",
        "text_rewrite": "text.rewrite",
        "text_formalize": "text.formalize",
        "text_simplify": "text.simplify",
        "text_professionalize": "text.rewrite",
        "text_translate": "text.translate",
        "text_summarize": "text.summarize",
        "text_summarize_executive": "text.summarize",
        "text_email_create": "text.email.create",
        "text_email_reply": "text.email.reply",
        "text_letter": "text.letter.create",
        "text_minutes": "text.minutes.create",
        "text_announcement": "text.announcement",
        "text_checklist": "text.checklist.create",
        "text_report": "text.report.create",
        "text_documentation": "text.documentation.create",
        "text_explain": "text.explain",
        "text_eli5": "text.eli5",
        "text_action_plan": "text.action_plan.create",
        "text_adapt_audience": "text.adapt_audience",
        "text_compare": "text.compare_versions",
        "text_extract_actions": "text.extract_actions",
        "text_tone_adjust": "text.change_tone",
        "text_table": "text.table.create",
        "text_memorandum": "text.memorandum.create",
        "text_conversation_doc": "text.conversation.transform",
        "text_three_versions": "text.compare_versions",
        "text_before_after": "text.compare_versions",
        "text_compose": "text.compose",
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
        audience = cls._detect_audience(normalized)

        if cls._wants_three_versions(normalized):
            subtype = "text_three_versions"

        if cls._wants_before_after(normalized):
            subtype = "text_before_after"

        return {
            "type": cls._CATEGORY_TO_TYPE.get(category, "compose"),
            "subtype": subtype,
            "category": category,
            "intent": cls._SUBTYPE_TO_INTENT.get(subtype, "text.compose"),
            "tone": tone,
            "audience": audience,
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
            "Modo especialista em textos (editor textual DELPI):",
            f"- Tipo: {ctx.get('type')} / subtipo: {ctx.get('subtype')}",
            "- Não consulte API, SQL, RAG ou web neste turno.",
            "- Preserve sentido, códigos, nomes, valores e siglas.",
        ]

        if ctx.get("deliverFinalOnly"):
            lines.append("- Entregue só a versão final, sem explicação longa.")

        if ctx.get("tone"):
            lines.append(f"- Tom desejado: {ctx['tone']}.")

        if ctx.get("audience"):
            lines.append(f"- Público-alvo: {ctx['audience']}.")

        template = cls._template_hint(ctx.get("subtype"))

        if template:
            lines.append(template)

        from app.domain.services.chat_text_editor_supplement_service import (
            ChatTextEditorSupplementService,
        )

        editor_block = ChatTextEditorSupplementService.build_block(ctx)

        if editor_block:
            lines.append(f"- {editor_block}")

        from app.domain.services.chat_text_context_resolver_service import (
            ChatTextContextResolverService,
        )

        text_context = ChatTextContextResolverService.resolve(
            message,
            previous_messages=previous_messages,
        )
        context_block = ChatTextContextResolverService.format_prompt_block(text_context)

        if context_block:
            lines.append(context_block)

        if cls._is_ambiguous_rewrite(message):
            lines.append(
                "- Pedido genérico: entregue versão inicial útil e ofereça refinamentos "
                "(formal, curto, direto) sem travar com perguntas."
            )

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

        payload: dict[str, Any] = {"textTask": ctx}
        from app.domain.services.chat_text_editor_supplement_service import (
            ChatTextEditorSupplementService,
        )

        payload["textAssistant"] = {
            "intent": ctx.get("intent"),
            "source": ctx.get("source"),
            "audience": ctx.get("audience"),
            "tone": ctx.get("tone"),
            "format": ctx.get("format"),
            "preserveMeaning": ctx.get("preserveMeaning"),
            "containsTechnicalTerms": ctx.get("containsTechnicalTerms"),
            "criticalDataPreserved": True,
            "suggestions": ctx.get("suggestions"),
        }

        if ChatTextEditorSupplementService.suggest_canvas_for_subtype(
            ctx.get("subtype"),
            answer=answer,
        ):
            payload["textCanvasSuggested"] = True

        return payload

    @classmethod
    def default_suggestions(cls, subtype: str | None) -> list[str]:
        by_subtype: dict[str, list[str]] = {
            "text_correct": [
                "Mostrar alterações",
                "Deixar mais formal",
                "Deixar mais direto",
                "Reescrever",
                "Colocar na lousa",
            ],
            "text_rewrite": [
                "Mostrar alterações",
                "Deixar mais formal",
                "Deixar mais direto",
                "Reescrever",
                "Colocar na lousa",
            ],
            "text_email_create": [
                "Deixar mais curto",
                "Deixar mais cordial",
                "Criar assunto alternativo",
                "Gerar 3 versões",
                "Colocar na lousa",
            ],
            "text_email_reply": [
                "Deixar mais curto",
                "Deixar mais cordial",
                "Criar assunto alternativo",
                "Colocar na lousa",
            ],
            "text_minutes": [
                "Extrair pendências",
                "Criar plano de ação",
                "Resumir para diretoria",
                "Colocar na lousa",
            ],
            "text_explain": [
                "Explicar simples",
                "ELI5",
                "Criar exemplo",
                "Criar checklist",
                "Criar documentação",
            ],
            "text_eli5": [
                "Explicar técnico",
                "Criar exemplo",
                "Criar glossário",
                "Colocar na lousa",
            ],
            "text_documentation": [
                "Deixar mais curto",
                "Criar checklist",
                "Colocar na lousa",
            ],
            "text_letter": [
                "Deixar mais formal",
                "Deixar mais curto",
                "Colocar na lousa",
            ],
            "text_report": [
                "Resumo executivo",
                "Transformar em e-mail",
                "Colocar na lousa",
            ],
        }

        if subtype and subtype in by_subtype:
            return by_subtype[subtype][:8]

        base = [
            "Deixar mais formal",
            "Deixar mais curto",
            "Deixar mais direto",
            "Deixar mais cordial",
            "Colocar na lousa",
            "Copiar texto",
        ]

        if subtype not in {"text_email_create", "text_email_reply"}:
            base.append("Criar e-mail")

        if subtype == "text_summarize":
            base.append("Resumo executivo")

        if subtype == "text_translate":
            base.append("Traduzir")

        return cls._dedupe(base)[:8]

    @staticmethod
    def _resolve_subtype(category: str, normalized: str) -> str:
        if category == "review":
            return "text_review_quality"

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

        if category == "letter":
            return "text_letter"

        if category == "report":
            return "text_report"

        if category == "documentation":
            if "faq" in normalized:
                return "text_documentation"

            return "text_documentation"

        if category == "explain":
            return "text_explain"

        if category == "eli5":
            return "text_eli5"

        if category == "action_plan":
            return "text_action_plan"

        if category == "adapt_audience":
            return "text_adapt_audience"

        if category == "to_table":
            return "text_table"

        if category == "memorandum":
            return "text_memorandum"

        if category == "conversation_transform":
            if "ata" in normalized or "reuni" in normalized:
                return "text_minutes"

            if "relat" in normalized:
                return "text_report"

            if "comunicado" in normalized:
                return "text_announcement"

            return "text_conversation_doc"

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
            if "comunicado" in normalized:
                return "text_announcement"

            return "text_compose"

        if category == "extract_actions":
            return "text_extract_actions"

        if category == "tone_adjust":
            return "text_tone_adjust"

        if "compare" in normalized or "compar" in normalized:
            return "text_compare"

        if "explique de forma simples" in normalized or "simplif" in normalized:
            return "text_simplify"

        if "antes e depois" in normalized or "o que mudou" in normalized:
            return "text_compare"

        if "plano de ação" in normalized or "plano de acao" in normalized:
            return "text_action_plan"

        return "text_compose"

    @staticmethod
    def _template_hint(subtype: str | None) -> str | None:
        hints = {
            "text_correct": "- Resposta: «Segue a versão corrigida:» + texto.",
            "text_review_quality": "- Avalie clareza, tom e estrutura; sugira versão melhorada.",
            "text_email_create": "- Inclua Assunto: e corpo; não invente assinatura.",
            "text_email_reply": "- Resposta a e-mail; preserve contexto do original.",
            "text_announcement": "- Use título # Comunicado e tom objetivo.",
            "text_letter": "- Carta formal: local/data, destinatário, corpo, fechamento; placeholders se faltar dado.",
            "text_minutes": "- Estrutura de ata: data, participantes, decisões, pendências.",
            "text_checklist": "- Lista com - [ ] e verbos de ação.",
            "text_report": "- Relatório: contexto, achados, conclusão; use «não informado» se faltar dado.",
            "text_documentation": "- Documentação: objetivo, escopo, passos; preserve termos técnicos.",
            "text_explain": "- Explicação clara; preserve precisão técnica.",
            "text_eli5": "- Linguagem simples e analogias; não distorça o conceito.",
            "text_action_plan": "- Tabela ação/responsável/prazo; não invente responsáveis.",
            "text_adapt_audience": "- Adapte vocabulário e tom ao público pedido.",
            "text_summarize": "- Resumo fiel; não invente fatos.",
            "text_compare": "- Seções Antes/Depois/O que mudou ou tabela comparativa.",
            "text_table": "- Entregue tabela markdown com cabeçalhos.",
            "text_memorandum": "- Memorando corporativo com Para/De/Assunto.",
            "text_conversation_doc": "- Documento a partir do histórico da conversa.",
            "text_three_versions": "- Três versões: Formal, Direta, Cordial.",
            "text_before_after": "- Antes / Depois / O que mudou.",
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
        if subtype in {
            "text_checklist",
            "text_minutes",
            "text_announcement",
            "text_report",
            "text_documentation",
            "text_action_plan",
            "text_letter",
        }:
            return "markdown"

        if subtype == "text_email_create" or subtype == "text_email_reply":
            return "email"

        if "tabela" in normalized:
            return "table"

        return "plain"

    @staticmethod
    def _detect_audience(normalized: str) -> str | None:
        if "diretoria" in normalized or "executiv" in normalized:
            return "executive"

        if "produção" in normalized or "producao" in normalized or "chão de fábrica" in normalized:
            return "production"

        if "cliente" in normalized:
            return "customer"

        if "fornecedor" in normalized:
            return "supplier"

        if "ti" in normalized or "engenharia" in normalized or "qualidade" in normalized:
            return "technical"

        if "rh" in normalized or "recursos humanos" in normalized:
            return "hr"

        return None

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
    def _wants_three_versions(normalized: str) -> bool:
        return any(
            phrase in normalized
            for phrase in (
                "3 versoes",
                "3 versões",
                "tres versoes",
                "três versões",
                "gerar 3",
                "gere 3",
            )
        )

    @staticmethod
    def _wants_before_after(normalized: str) -> bool:
        return any(
            phrase in normalized
            for phrase in (
                "antes e depois",
                "antes/depois",
                "o que mudou",
                "mostre alteracoes",
                "mostre alterações",
            )
        )

    @staticmethod
    def _is_ambiguous_rewrite(message: str | None) -> bool:
        normalized = (message or "").strip().lower()

        if len(normalized) > 80:
            return False

        return normalized.startswith("melhore") and ":" not in normalized

    @staticmethod
    def _has_technical_terms(text: str) -> bool:
        return bool(
            re.search(
                r"\b(BOM|OV|LMP|RBAC|API|SQL|ERP|Protheus|\d{5,})\b",
                text,
                re.IGNORECASE,
            )
        )

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
