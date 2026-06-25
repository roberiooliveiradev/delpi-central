"""Síntese da resposta à pergunta do usuário a partir dos dados da API — Playbook 13."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_question_synthesis_content_service import (
    ChatOperationalQuestionSynthesisContentService,
)
from app.domain.services.chat_operational_commentary_profile_service import (
    ChatOperationalCommentaryProfileService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_production_schedule_membership_presentation_service import (
    ChatProductionScheduleMembershipPresentationService,
)
from app.domain.services.external_actions.operational_route_narrative_service import (
    ExternalActionOperationalRouteNarrativeService,
)

_Narrative = ExternalActionOperationalRouteNarrativeService
_Content = ChatOperationalQuestionSynthesisContentService


class ChatOperationalUserQuestionSynthesisService:
    """Extrai conclusão legível da pergunta — não repete contagem bruta da API."""

    @classmethod
    def apply(
        cls,
        commentary: dict[str, Any],
        *,
        data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        user_message: str | None = None,
        profile_key: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(commentary, dict) or not isinstance(data, dict):
            return commentary

        message = str(user_message or "").strip()

        if not message:
            meta = metadata if isinstance(metadata, dict) else {}
            message = str(meta.get("userMessage") or "").strip()

        if not message:
            return commentary

        meta = metadata if isinstance(metadata, dict) else {}

        from app.domain.services.chat_presentation_prose_delivery_service import (
            ChatPresentationProseDeliveryService,
        )

        if ChatPresentationProseDeliveryService.should_skip_question_synthesis_verdict(meta):
            commentary["questionSynthesis"] = {
                "applied": False,
                "skipped": "template_profile_verdict",
            }
            return commentary

        profile = str(profile_key or commentary.get("profileKey") or "").strip()
        entity = cls._resolve_entity(metadata, data)
        synthesis = cls.try_synthesize(
            message,
            data,
            profile_key=profile,
            entity=entity,
        )

        if not synthesis:
            return commentary

        primary = str(synthesis.get("summary") or "").strip()

        if primary:
            commentary["summary"] = primary
            commentary["highlights"] = [primary]
            summary_lines = [primary]
            summary_lines.extend(
                line
                for line in (commentary.get("highlights") or [])
                if str(line or "").strip() and str(line).strip() != primary
            )
            commentary["summaryLines"] = summary_lines[:4]

        interpretation = str(synthesis.get("interpretation") or "").strip()

        if interpretation:
            commentary["interpretation"] = interpretation

        if synthesis.get("attention"):
            existing = [
                str(line).strip()
                for line in (commentary.get("attention") or [])
                if str(line or "").strip()
            ]
            merged = existing[:]

            for line in synthesis["attention"]:
                token = str(line or "").strip()

                if token and token not in merged:
                    merged.append(token)

            commentary["attention"] = merged[:6]

        commentary["questionSynthesis"] = {
            "intent": synthesis.get("intent"),
            "applied": True,
        }

        return commentary

    @classmethod
    def try_synthesize(
        cls,
        user_message: str,
        data: dict[str, Any],
        *,
        profile_key: str = "",
        entity: str = "",
    ) -> dict[str, Any] | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(user_message)

        membership = cls._synthesize_schedule_membership(user_message, data, entity=entity)

        if membership:
            return membership

        synthesis_strategy = ChatOperationalCommentaryProfileService.question_synthesis_strategy(
            profile_key
        )

        if synthesis_strategy == "structure_exclusivity" or (
            not synthesis_strategy
            and (
                entity == "product_structure_exclusivity"
                or ChatProductQueryIntentService._looks_like_structure_exclusivity_question(
                    normalized
                )
            )
        ):
            return cls._synthesize_structure_exclusivity(data, user_message)

        if synthesis_strategy == "production_status" or (
            not synthesis_strategy
            and (
                entity == "product_production_status"
                or ChatProductQueryIntentService._looks_like_production_status_question(
                    normalized
                )
            )
        ):
            return cls._synthesize_production_status(data, user_message, normalized)

        return None

    @classmethod
    def _synthesize_schedule_membership(
        cls,
        user_message: str,
        data: dict[str, Any],
        *,
        entity: str,
    ) -> dict[str, Any] | None:
        if entity != "production_schedule_today" and not (
            ChatProductionScheduleMembershipPresentationService.looks_like_membership_question(
                user_message
            )
        ):
            return None

        report = ChatProductionScheduleMembershipPresentationService.try_build_membership_answer(
            data,
            message=user_message,
        )

        if not report:
            return None

        lines = [
            str(line).strip()
            for line in (report.get("linhas") or [])
            if str(line or "").strip()
        ]

        if not lines:
            return None

        primary = re.sub(r"^-\s*", "", lines[0])
        interpretation = "\n".join(
            re.sub(r"^-\s*", "", line) for line in lines[1:4]
        ).strip()

        return {
            "intent": "schedule_membership",
            "summary": primary,
            "interpretation": interpretation,
        }

    @classmethod
    def _synthesize_structure_exclusivity(
        cls,
        data: dict[str, Any],
        user_message: str,
    ) -> dict[str, Any] | None:
        product = data.get("product") if isinstance(data.get("product"), dict) else {}
        summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
        code = str(product.get("product_code") or product.get("code") or "").strip()
        exclusive_count = int(summary.get("total_exclusive_raw_materials") or 0)
        mp_count = int(summary.get("total_raw_materials") or 0)
        normalized = ChatMessageNormalizationService.normalize_for_matching(user_message)
        exclusive_mps = cls._exclusive_mp_items(data)

        if exclusive_count > 0:
            if len(exclusive_mps) == 1:
                item = exclusive_mps[0]
                primary = _Content.format(
                    "structureExclusivity",
                    "exclusiveYesSingle",
                    count=str(exclusive_count),
                    code=code or "—",
                    mpCode=str(
                        item.get("product_code") or item.get("component_code") or "—"
                    ),
                    description=str(
                        item.get("description") or item.get("component_description") or "—"
                    ),
                )
            else:
                listing = cls._format_exclusive_mp_list(exclusive_mps)
                primary = _Content.format(
                    "structureExclusivity",
                    "exclusiveYesNamed",
                    count=str(exclusive_count),
                    code=code or "—",
                    list=listing,
                )
        else:
            primary = _Content.format(
                "structureExclusivity",
                "exclusiveNo",
                count=str(mp_count),
                code=code or "—",
            )

        interpretation = ""

        if any(
            term in normalized
            for term in ("compos", "compoem", "quais mp", "matérias-primas", "materias-primas")
        ):
            interpretation = _Content.format(
                "structureExclusivity",
                "compositionAsk",
                code=code or "—",
                total=str(summary.get("total_components") or 0),
                intermediates=str(summary.get("total_intermediates") or 0),
                rawMaterials=str(mp_count),
            )

        return {
            "intent": "structure_exclusivity",
            "summary": primary,
            "interpretation": interpretation,
        }

    @classmethod
    def _synthesize_production_status(
        cls,
        data: dict[str, Any],
        user_message: str,
        normalized: str,
    ) -> dict[str, Any] | None:
        product = data.get("product") if isinstance(data.get("product"), dict) else {}
        summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
        items = data.get("items") if isinstance(data.get("items"), list) else []
        code = str(product.get("product_code") or product.get("code") or "").strip()
        reference_date = str(data.get("reference_date") or "").strip()

        pa_started = _Narrative.format_production_flag(summary.get("pa_production_started"))
        pi_started = _Narrative.format_production_flag(summary.get("pi_production_started"))
        pa_qty = str(summary.get("total_pa_reported_quantity") or 0)
        pi_qty = str(summary.get("total_pi_reported_quantity") or 0)

        if cls._asks_open_op(normalized) or cls._asks_production_started(normalized):
            return cls._synthesize_production_op_answer(
                items,
                normalized,
                reference_date=reference_date,
            )

        if reference_date:
            primary = _Content.format(
                "productionStatus",
                "situationSummary",
                code=code or "—",
                paStarted=pa_started,
                piStarted=pi_started,
                paQty=pa_qty,
                piQty=pi_qty,
                date=reference_date,
            )
        else:
            primary = _Content.format(
                "productionStatus",
                "situationSummaryNoDate",
                code=code or "—",
                paStarted=pa_started,
                piStarted=pi_started,
                paQty=pa_qty,
                piQty=pi_qty,
            )

        return {
            "intent": "production_status",
            "summary": primary,
        }

    @classmethod
    def _synthesize_production_op_answer(
        cls,
        items: list[Any],
        normalized: str,
        *,
        reference_date: str,
    ) -> dict[str, Any]:
        pa_order = cls._primary_pa_order(items)

        if not pa_order:
            return {
                "intent": "production_open_op",
                "summary": _Content.format("productionStatus", "openOpNo"),
            }

        order = str(pa_order.get("production_order") or "").strip()
        started = _Narrative.format_production_flag(pa_order.get("production_started"))
        reported = str(pa_order.get("reported_quantity") or 0)

        if cls._asks_appointment(normalized) and started == "Sim":
            try:
                reported_qty = float(str(pa_order.get("reported_quantity") or 0).replace(",", "."))
            except ValueError:
                reported_qty = 0.0

            if reported_qty <= 0:
                return {
                    "intent": "production_appointment",
                    "summary": _Content.format("productionStatus", "reportedNone"),
                }

        if order and started == "Sim":
            return {
                "intent": "production_open_op",
                "summary": _Content.format(
                    "productionStatus",
                    "openOpYesStarted",
                    order=order,
                    reported=reported,
                ),
            }

        if order:
            return {
                "intent": "production_open_op",
                "summary": _Content.format(
                    "productionStatus",
                    "openOpYesNotStarted",
                    order=order,
                ),
            }

        if cls._asks_production_started(normalized):
            if started == "Sim":
                return {
                    "intent": "production_started",
                    "summary": _Content.format(
                        "productionStatus",
                        "startedYes",
                        order=order or "—",
                        reported=reported,
                    ),
                }

            return {
                "intent": "production_started",
                "summary": _Content.format("productionStatus", "startedNo"),
            }

        return {
            "intent": "production_open_op",
            "summary": _Content.format("productionStatus", "openOpNo"),
        }

    @classmethod
    def _primary_pa_order(cls, items: list[Any]) -> dict[str, Any] | None:
        for item in items:
            if not isinstance(item, dict):
                continue

            product_type = str(item.get("product_type") or "").upper()
            level = item.get("level")

            if product_type == "PA" or level in {0, "0", "0.0"}:
                return item

        for item in items:
            if isinstance(item, dict) and str(item.get("production_order") or "").strip():
                return item

        return None

    @staticmethod
    def _asks_open_op(normalized: str) -> bool:
        return any(
            token in normalized
            for token in (
                "op aberta",
                "tem op",
                "ordem aberta",
                "ordem de producao aberta",
            )
        )

    @staticmethod
    def _asks_production_started(normalized: str) -> bool:
        return any(
            token in normalized
            for token in (
                "iniciou producao",
                "iniciou produção",
                "comecou a produzir",
                "começou a produzir",
                "ja comecou",
                "já começou",
                "producao iniciada",
                "produção iniciada",
            )
        )

    @staticmethod
    def _asks_appointment(normalized: str) -> bool:
        return any(
            token in normalized
            for token in (
                "apontamento",
                "apontou",
                "ja apontou",
                "já apontou",
            )
        )

    @staticmethod
    def _exclusive_mp_items(data: dict[str, Any]) -> list[dict[str, Any]]:
        from app.domain.services.external_actions.presenters.product_operational_table_row_enrichment import (
            is_exclusive_raw_material_item,
        )

        items = data.get("items") if isinstance(data.get("items"), list) else []

        return [
            item
            for item in items
            if isinstance(item, dict)
            and str(item.get("component_type") or "").upper() == "MP"
            and is_exclusive_raw_material_item(item)
        ]

    @staticmethod
    def _format_exclusive_mp_list(items: list[dict[str, Any]], *, preview_limit: int = 6) -> str:
        parts: list[str] = []

        for item in items[:preview_limit]:
            code = str(item.get("product_code") or item.get("component_code") or "—")
            description = str(
                item.get("description") or item.get("component_description") or ""
            ).strip()
            parts.append(f"**{code}** ({description})" if description else f"**{code}**")

        remaining = len(items) - preview_limit

        if remaining > 0:
            parts.append(f"… e mais **{remaining}**")

        return "; ".join(parts)

    @staticmethod
    def _resolve_entity(metadata: dict[str, Any] | None, data: dict[str, Any]) -> str:
        if isinstance(metadata, dict):
            api_meta = metadata.get("apiDelpiResponseMeta")

            if isinstance(api_meta, dict):
                token = str(api_meta.get("entity") or "").strip()

                if token:
                    return token

        entity = data.get("entity")

        return str(entity or "").strip()
