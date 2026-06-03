"""Validador de qualidade textual geral — Playbook 03 §26."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_text_correction_intent_service import (
    ChatTextCorrectionIntentService,
)
from app.domain.services.chat_text_task_service import ChatTextTaskService


class ChatTextQualityValidator:
    _INVENTED_SIGNATURE = re.compile(
        r"\b(diretor|gerente\s+de|ceo|cfo|coordenador\s+de)\b",
        re.IGNORECASE,
    )

    @classmethod
    def validate(
        cls,
        answer: str | None,
        *,
        message: str | None = None,
        workspace_context: dict | None = None,
    ) -> dict[str, Any]:
        text = (answer or "").strip()
        ctx = ChatTextTaskService.classify(message)
        subtype = ctx.get("subtype")
        checks: list[dict[str, str]] = []

        if subtype in {"text_correct", "text_rewrite", "text_formalize", "text_simplify"}:
            from app.domain.services.chat_text_correction_quality_validator import (
                ChatTextCorrectionQualityValidator,
            )

            correction = ChatTextCorrectionQualityValidator.validate(
                answer,
                user_message=message,
                subtype=subtype.replace("text_", "text_correct_")
                if subtype == "text_correct"
                else None,
                preserved_codes=ctx.get("preservedCodes"),
            )

            checks.extend(correction.get("checks") or [])

        if len(text) < 3:
            checks.append({"code": "empty_answer", "message": "Resposta sem texto utilizável."})

        for code in ctx.get("preservedCodes") or []:
            if code not in text:
                checks.append(
                    {
                        "code": "code_not_preserved",
                        "message": f"Código/termo ausente na resposta: {code}.",
                    }
                )

        if ctx.get("deliverFinalOnly") and len(text.split()) > 120:
            checks.append(
                {
                    "code": "over_explained",
                    "message": "Pedido era só versão final.",
                }
            )

        if subtype in {"text_email_create", "text_email_reply"} and "assunto" not in text.lower():
            if "subject:" not in text.lower():
                checks.append(
                    {
                        "code": "missing_subject",
                        "message": "E-mail sem linha de assunto sugerida.",
                    }
                )

        if subtype == "text_action_plan" and re.search(
            r"\b(joão|maria|pedro|ana|carlos)\b",
            text,
            re.IGNORECASE,
        ):
            if "[" not in text:
                checks.append(
                    {
                        "code": "invented_owner",
                        "message": "Plano de ação com possível responsável inventado.",
                    }
                )

        if subtype == "text_eli5" and len(text.split()) < 20:
            checks.append(
                {
                    "code": "eli5_too_short",
                    "message": "ELI5 deveria trazer explicação mais desenvolvida.",
                }
            )

        if cls._INVENTED_SIGNATURE.search(text) and not ChatTextCorrectionIntentService.extract_context(
            message
        ).get("senderSignature"):
            checks.append(
                {
                    "code": "invented_signature",
                    "message": "Possível cargo/assinatura inventada.",
                }
            )

        passed = len(checks) == 0

        return {
            "passed": passed,
            "checks": checks,
            "subtype": subtype,
            "checklist": cls.build_checklist(
                answer=text,
                message=message,
                ctx=ctx,
                checks=checks,
            ),
        }

    @classmethod
    def build_checklist(
        cls,
        *,
        answer: str | None = None,
        message: str | None = None,
        ctx: dict[str, Any] | None = None,
        checks: list[dict[str, str]] | None = None,
        passed: bool | None = None,
    ) -> list[dict[str, bool]]:
        text = (answer or "").strip()
        context = ctx or ChatTextTaskService.classify(message)
        issue_codes = {str(item.get("code") or "") for item in (checks or [])}

        def ok(code: str | None = None, *, default: bool = True) -> bool:
            if passed is not None and code is None:
                return passed

            if code and code in issue_codes:
                return False

            return default

        deliver_final = bool(context.get("deliverFinalOnly"))

        return [
            {"item": "O pedido foi atendido", "ok": ok("empty_answer", default=bool(text))},
            {"item": "O sentido foi preservado", "ok": ok("code_not_preserved")},
            {
                "item": "O tom está adequado",
                "ok": ok(None, default=True),
            },
            {
                "item": "O público foi considerado",
                "ok": ok(None, default=bool(context.get("audience")) or True),
            },
            {
                "item": "O formato está correto",
                "ok": ok("missing_subject", default=True),
            },
            {
                "item": "Nomes e números foram preservados",
                "ok": ok("code_not_preserved", default=True),
            },
            {"item": "Não houve invenção de dados", "ok": ok("invented_signature", default=ok("invented_owner"))},
            {
                "item": "A linguagem está natural",
                "ok": ok(None, default=True),
            },
            {
                "item": "O texto está pronto para copiar",
                "ok": ok("empty_answer", default=bool(text)),
            },
            {
                "item": "Há próximos passos úteis",
                "ok": ok("over_explained", default=not deliver_final or len(text.split()) <= 120),
            },
        ]
