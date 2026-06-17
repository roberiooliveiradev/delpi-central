"""Resposta objetiva: PA está na programação de hoje? OP e quantidade."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ChatProductionScheduleMembershipPresentationService:
    @classmethod
    def looks_like_membership_question(cls, message: str | None) -> bool:
        return ChatProductQueryIntentService.looks_like_production_schedule_membership_question(
            message
        )

    @classmethod
    def blocks_presentation_only_shortcut(cls, message: str | None) -> bool:
        return cls.looks_like_membership_question(message)

    @classmethod
    def resolve_detail_filter(
        cls,
        message: str | None,
        *,
        path: str = "",
    ) -> dict[str, str] | None:
        normalized_path = str(path or "").lower()
        schedule_path = "/production/schedule/" in normalized_path
        sql_path = "/data/sql" in normalized_path

        if not schedule_path and not sql_path and not cls.looks_like_membership_question(message):
            return None

        filter_code = ChatProductQueryIntentService.resolve_schedule_product_filter_code(message)

        if not filter_code:
            return None

        if len(filter_code) < 8 and not cls.looks_like_membership_question(message):
            return None

        return {"product_code_prefix": filter_code}

    @classmethod
    def try_build_playbook_report(
        cls,
        root: dict,
        *,
        entity: str,
        message: str | None = None,
    ) -> dict[str, Any] | None:
        if entity != "production_schedule_today" or not isinstance(root, dict):
            return None

        return cls.try_build_membership_answer(root, message=message)

    @classmethod
    def try_build_membership_answer(
        cls,
        root: dict,
        *,
        message: str | None = None,
    ) -> dict[str, Any] | None:
        if not isinstance(root, dict):
            return None

        query_context = root.get("query_context")
        product_code = ""

        if isinstance(query_context, dict):
            product_code = re.sub(
                r"\D",
                "",
                str(query_context.get("product_code_prefix") or ""),
            )

        if len(product_code) < 8 and message:
            filter_code = ChatProductQueryIntentService.resolve_schedule_product_filter_code(
                message
            )
            product_code = re.sub(r"\D", "", filter_code or "")

        if len(product_code) < 8:
            return None

        if not isinstance(query_context, dict):
            root = dict(root)
            root["query_context"] = {"product_code_prefix": product_code}

        reference_date = str(root.get("reference_date") or "").strip()
        items = cls._schedule_items(root)
        matching = [
            cls.normalize_schedule_item(item)
            for item in items
            if isinstance(item, dict)
            and cls._item_matches_product_code(item, product_code)
        ]

        title = ExternalActionResponseContentService.format(
            "productionSchedule",
            "membership",
            "titleWithCode",
            code=product_code,
        )
        linhas: list[str] = []

        if matching:
            linhas.append(
                ExternalActionResponseContentService.format(
                    "productionSchedule",
                    "membership",
                    "foundLine",
                    code=product_code,
                    reference_date=reference_date or "hoje",
                )
            )

            for item in matching[:6]:
                line = cls._format_order_line(item)

                if line:
                    linhas.append(f"- {line}")
        else:
            linhas.append(
                ExternalActionResponseContentService.format(
                    "productionSchedule",
                    "membership",
                    "notFoundLine",
                    code=product_code,
                    reference_date=reference_date or "hoje",
                )
            )

        return {
            "titulo": title,
            "linhas": linhas,
            "dados": root,
        }

    @classmethod
    def _schedule_items(cls, root: dict) -> list[dict[str, Any]]:
        items = root.get("items")

        if isinstance(items, list) and items:
            return [item for item in items if isinstance(item, dict)]

        rows: list[dict[str, Any]] = []
        resultsets = root.get("resultsets")

        if isinstance(resultsets, list):
            for resultset in resultsets:
                if not isinstance(resultset, dict):
                    continue

                batch = resultset.get("rows")

                if isinstance(batch, list):
                    rows.extend(item for item in batch if isinstance(item, dict))

        return rows

    @classmethod
    def normalize_schedule_item(cls, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "product_code": cls._field(
                item,
                "product_code",
                "COD_PRODUTO",
                "cod_produto",
                "C2_PRODUTO",
            ),
            "production_order": cls._field(
                item,
                "production_order",
                "C2_OP",
                "c2_op",
                "OP",
            ),
            "planned_qty": item.get("planned_qty")
            if item.get("planned_qty") is not None
            else item.get("QTD_PLANEJADA", item.get("qtd_planejada")),
            "unit": cls._field(item, "unit", "UNIDADE", "unidade", "C2_UM"),
            "branch": cls._field(item, "branch", "FILIAL", "filial", "C2_FILIAL"),
        }

    @staticmethod
    def _field(item: dict[str, Any], *keys: str) -> str:
        for key in keys:
            value = item.get(key)

            if value is not None and str(value).strip():
                return str(value).strip()

        return ""

    @classmethod
    def _item_matches_product_code(cls, item: dict[str, Any], product_code: str) -> bool:
        normalized = cls.normalize_schedule_item(item)
        token = re.sub(r"\D", "", str(normalized.get("product_code") or ""))

        if len(product_code) >= 8:
            return token == product_code

        return token.startswith(product_code)

    @classmethod
    def _format_order_line(cls, item: dict[str, Any]) -> str:
        normalized = cls.normalize_schedule_item(item)
        production_order = str(normalized.get("production_order") or "").strip()
        planned_qty = normalized.get("planned_qty")
        unit = str(normalized.get("unit") or "").strip()
        branch = str(normalized.get("branch") or "").strip()

        if not production_order:
            return ""

        qty_text = ExternalActionColumnLabelService.format_num(planned_qty)
        unit_suffix = f" {unit}".rstrip()
        line = ExternalActionResponseContentService.format(
            "productionSchedule",
            "membership",
            "orderLine",
            production_order=production_order,
            planned_qty=qty_text,
            unit_suffix=unit_suffix,
        )

        if branch:
            line += ExternalActionResponseContentService.format(
                "productionSchedule",
                "membership",
                "branchSuffix",
                branch=branch,
            )

        return line
