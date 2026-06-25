"""Pendências ativas do turno (Playbook 01) — parâmetro faltante e respostas curtas."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatActivePendingService:
    _ROUTING_FEEDBACK_REASONS = frozenset(
        {
            "wrong_query",
            "lost_context",
            "wrong_product",
            "wrong_intent",
            "bad_format",
            "forgot_previous",
            "routing_wrong_intent",
            "routing_wrong_api",
            "routing_should_api",
            "routing_should_not_api",
            "routing_should_web",
            "routing_unneeded_web",
            "routing_lost_context",
            "routing_repeated_question",
            "routing_wrong_format",
            "routing_missed_text_task",
        }
    )

    @classmethod
    def attach_for_operational_direct_answer(
        cls,
        metadata: dict,
        *,
        message: str,
        previous_messages: list[Any] | None,
        pipeline_stages: list[str] | None,
    ) -> None:
        stages = list(pipeline_stages or [])

        if "operational_parameter" not in stages:
            return

        pending = cls.describe_pending_for_question(
            message,
            previous_messages=previous_messages,
        )

        if pending:
            metadata["activePending"] = pending

    @classmethod
    def describe_pending_for_question(
        cls,
        message: str,
        *,
        previous_messages: list[Any] | None,
    ) -> dict[str, Any] | None:
        from app.domain.services.chat_operational_parameter_service import (
            ChatOperationalParameterService,
        )

        if ChatOperationalParameterService.resolve_missing_product_code_answer(
            message,
            previous_messages=previous_messages,
        ):
            from app.domain.services.chat_active_query_session_service import (
                ChatActiveQuerySessionService,
            )

            intent = ChatOperationalParameterService._missing_product_code_intent(
                message,
                None,
                previous_messages=previous_messages,
            )

            context = ChatActiveQuerySessionService.build_pending_context(
                message,
                sub_intent=intent or "default",
                expected_param="productCode",
            )

            return {
                "kind": "missing_product_code",
                "expectedParam": "productCode",
                "subIntent": intent or "default",
                "prompt": "Informe o código do produto para continuar a consulta.",
                "context": context,
            }

        if ChatOperationalParameterService.resolve_ambiguous_period_answer(
            message,
            previous_messages=previous_messages,
        ):
            from datetime import date

            from app.domain.services.chat_date_range_intent_service import (
                ChatDateRangeIntentService,
            )

            ambiguous = ChatDateRangeIntentService.detect_ambiguous_named_month(
                message,
                today=date.today(),
            )

            context: dict[str, Any] = {}

            if ambiguous:
                context = {
                    "monthLabel": ambiguous.month_label,
                    "currentYear": ambiguous.current_year,
                    "previousYear": ambiguous.previous_year,
                }

            return {
                "kind": "ambiguous_period_year",
                "expectedParam": "periodYear",
                "subIntent": "period",
                "prompt": "Confirme o ano do período solicitado.",
                "context": context,
            }

        missing_date = ChatOperationalParameterService.resolve_missing_date_answer(
            message,
            previous_messages=previous_messages,
        )

        if missing_date:
            from app.domain.services.chat_operational_date_parameter_service import (
                ChatOperationalDateParameterService,
            )

            context = ChatOperationalDateParameterService.build_pending_context(
                message,
                previous_messages=previous_messages,
            )

            return {
                "kind": "missing_date",
                "expectedParam": "period",
                "subIntent": context.get("subIntent") or "default",
                "prompt": "Informe a data ou o período da consulta.",
                "context": context,
            }

        return None

    @classmethod
    def find_from_messages(cls, previous_messages: list[Any] | None) -> dict[str, Any] | None:
        for item in reversed(previous_messages or []):
            role = str(getattr(item, "role", None) or (item.get("role") if isinstance(item, dict) else "") or "")

            if role != "assistant":
                continue

            meta = getattr(item, "metadata", None)

            if meta is None and isinstance(item, dict):
                meta = item.get("metadata")

            if not isinstance(meta, dict):
                continue

            pending = meta.get("activePending")

            if isinstance(pending, dict) and pending.get("kind"):
                return dict(pending)

        return None

    @classmethod
    def try_resolve(cls, message: str, pending: dict[str, Any]) -> dict[str, Any] | None:
        kind = str(pending.get("kind") or "").strip()
        normalized = str(message or "").strip()

        if not normalized or not kind:
            return None

        if kind == "missing_product_code":
            if ChatProductQueryIntentService.looks_like_scope_reset_operational_query(
                normalized
            ):
                return None

            from app.domain.services.chat_analysis_intent_service import (
                ChatAnalysisIntentService,
            )

            codes = ChatAnalysisIntentService.extract_all_product_codes(normalized)

            if not codes:
                code = ChatProductQueryIntentService.extract_product_code(normalized)

                if not code and re.fullmatch(r"\d{5,}", normalized.replace(".", "")):
                    code = normalized.replace(".", "").strip()

                if code and ChatProductQueryIntentService._CALENDAR_YEAR_RE.fullmatch(code):
                    return None

                if code:
                    codes = [code]

            if codes:
                context = (
                    pending.get("context")
                    if isinstance(pending.get("context"), dict)
                    else {}
                )
                original_message = str(context.get("originalMessage") or "").strip()
                resume_message = f"{original_message} {normalized}".strip()
                resolved_params: dict[str, str] = {}

                if len(codes) == 1:
                    resolved_params["productCode"] = codes[0]
                else:
                    resolved_params["productCode"] = codes[0]
                    resolved_params["productCodes"] = ",".join(codes)

                return {
                    "kind": kind,
                    "resolvedParams": resolved_params,
                    "resumeMessage": resume_message,
                    "requiresTool": True,
                }

        if kind == "ambiguous_period_year":
            from app.domain.services.chat_date_range_intent_service import (
                ChatDateRangeIntentService,
            )

            if ChatDateRangeIntentService.is_year_clarification_reply(
                normalized,
                [{"role": "assistant", "metadata": {"activePending": pending}}],
            ):
                year_match = re.search(r"(20\d{2})", normalized)

                if year_match:
                    return {
                        "kind": kind,
                        "resolvedParams": {"periodYear": year_match.group(1)},
                        "requiresTool": True,
                    }

        if kind == "missing_date":
            from app.domain.services.chat_operational_date_parameter_service import (
                ChatOperationalDateParameterService,
            )

            date_range = ChatOperationalDateParameterService.resolve_date_range(normalized)

            if date_range:
                context = pending.get("context") if isinstance(pending.get("context"), dict) else {}
                original_message = str(context.get("originalMessage") or "").strip()
                resume_message = f"{original_message} {normalized}".strip()
                resolved_params = {
                    "referenceDate": date_range.start_date,
                    "dateStart": date_range.start_date,
                    "dateEnd": date_range.end_date,
                }
                product_code = str(context.get("productCode") or "").strip()

                if product_code:
                    resolved_params["productCode"] = product_code

                return {
                    "kind": kind,
                    "resolvedParams": resolved_params,
                    "resumeMessage": resume_message,
                    "requiresTool": True,
                }

        if kind in {"branch", "missing_branch", "filial"}:
            branch_match = re.search(r"\b(\d{1,3})\b", normalized)

            if branch_match:
                return {
                    "kind": kind,
                    "resolvedParams": {"branch": branch_match.group(1)},
                    "requiresTool": True,
                }

            lowered = normalized.lower()

            if lowered in {"sim", "s", "yes", "ok", "pode", "pode seguir"}:
                options = pending.get("options")

                branch = "01"

                if isinstance(options, list) and options:
                    branch = str(options[0]).strip() or branch

                return {
                    "kind": kind,
                    "resolvedParams": {"branch": branch},
                    "requiresTool": True,
                }

        return None

    @classmethod
    def routing_snapshot_from_assistant_metadata(
        cls,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(metadata, dict):
            return None

        admin_debug = metadata.get("adminDebug")

        if not isinstance(admin_debug, dict):
            return None

        intent_route = admin_debug.get("intentRoute")

        return dict(intent_route) if isinstance(intent_route, dict) else None

    @classmethod
    def should_attach_routing_snapshot(cls, reason: str | None) -> bool:
        return str(reason or "").strip() in cls._ROUTING_FEEDBACK_REASONS
