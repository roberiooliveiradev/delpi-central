"""Visão geral e detalhes cadastrais de produto — Fase 3A lote 15."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionProductOverviewPresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _overview_missing(self) -> str:
        return self._host._presenter_text("productOverview", "missingValue")

    def _build_product_overview_narrative_lines(self, product: dict, root: dict) -> list[str]:
        code = str(product.get("code") or "").strip()
        description = str(product.get("description") or "").strip()
        product_type = str(product.get("type") or "").strip()
        unit = str(product.get("unit") or "").strip()
        group_code = str(product.get("group_code") or "").strip()
        active = str(product.get("active") or "").strip()
        warehouse = str(product.get("default_warehouse") or "").strip()
        missing = self._overview_missing()

        lines = [
            self._host._presenter_text(
                "productOverview",
                "identityLine",
                code=code,
                description=description
                or self._host._presenter_text("productOverview", "noDescription"),
            ),
            self._host._presenter_text(
                "productOverview",
                "classificationLine",
                type=product_type or missing,
                unit=unit or missing,
                group_code=group_code or missing,
            ),
            self._host._presenter_text("productOverview", "cadastralActive", active=active or missing)
            + (
                self._host._presenter_text(
                    "productOverview",
                    "cadastralWarehouseSuffix",
                    warehouse=warehouse,
                )
                if warehouse
                else self._host._presenter_text("productOverview", "cadastralEnd")
            ),
        ]

        purchase_price = product.get("last_purchase_price")
        purchase_date = str(product.get("last_purchase_date") or "").strip()
        standard_cost = product.get("standard_cost")

        if purchase_price in (0, 0.0, None) and not purchase_date:
            lines.append(self._host._analyser_markdown("noRecentPurchase"))
        else:
            price_text = self._host._format_currency(purchase_price)
            date_text = self._format_revision_date(purchase_date) if purchase_date else ""
            date_suffix = (
                self._host._presenter_text(
                    "productOverview",
                    "lastPurchaseDateSuffix",
                    date=date_text,
                )
                if date_text
                else ""
            )
            lines.append(
                self._host._presenter_text(
                    "productOverview",
                    "lastPurchase",
                    price=price_text,
                    date_suffix=date_suffix,
                )
            )

        if standard_cost not in (None, ""):
            lines.append(
                self._host._analyser_markdown(
                    "standardCost",
                    cost=self._host._format_currency(standard_cost),
                )
            )

        revision = str(product.get("last_revision_date") or "").strip()
        ncm = str(product.get("ncm_ipi_position") or "").strip()

        if revision:
            lines.append(
                self._host._presenter_text(
                    "productOverview",
                    "revisionLine",
                    revision=self._format_revision_date(revision),
                )
            )

        if ncm:
            lines.append(
                self._host._presenter_text("productOverview", "ncmLine", ncm=ncm)
            )

        blocked = str(product.get("blocked") or "").strip()
        if blocked and blocked not in {"N", "0", ""}:
            lines.append(
                self._host._presenter_text(
                    "productOverview",
                    "blockedLine",
                    blocked=blocked,
                )
            )

        for key in ["guide", "inspection", "structure", "customers", "suppliers"]:
            value = root.get(key)
            if isinstance(value, dict):
                total = value.get("total")
                if total is not None:
                    label = self._host._label_collection(key)
                    from app.domain.services.chat_product_operational_content_service import (
                        ChatProductOperationalContentService,
                    )

                    if int(total or 0) == 0:
                        lines.append(
                            ChatProductOperationalContentService.format(
                                "presenter",
                                "profile",
                                "collectionEmpty",
                                label=label,
                            )
                        )
                    else:
                        lines.append(
                            ChatProductOperationalContentService.format(
                                "presenter",
                                "profile",
                                "collectionWithTotal",
                                label=label,
                                total=total,
                            )
                        )

        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )

        lines.append(
            ChatProductOperationalContentService.get("presenter", "profile", "nextStepsHint")
        )

        return lines

    @staticmethod
    def _format_revision_date(token: str) -> str:
        raw = str(token or "").strip()

        if len(raw) == 8 and raw.isdigit():
            return f"{raw[6:8]}/{raw[4:6]}/{raw[0:4]}"

        return raw

    def _present_product(self, root: dict, product: dict) -> dict:
        product_summary = {
            "code": product.get("code"),
            "description": product.get("description"),
            "type": product.get("type"),
            "unit": product.get("unit"),
            "groupCode": product.get("group_code"),
            "active": product.get("active"),
            "defaultWarehouse": product.get("default_warehouse"),
            "lastPurchasePrice": product.get("last_purchase_price"),
            "standardCost": product.get("standard_cost"),
            "lastRevisionDate": product.get("last_revision_date"),
            "ncm": product.get("ncm_ipi_position"),
        }

        detail_list = self._extract_product_detail_list(root)

        if detail_list:
            return self._present_product_with_details(product_summary, detail_list, root)

        linhas = self._build_product_overview_narrative_lines(product, root)

        return {
            "titulo": self._host._presenter_text(
                "productPresentationTitles",
                "overviewWithCode",
                code=str(product_summary["code"]),
            ),
            "linhas": [line for line in linhas if "None" not in line],
            "campos": self._host._alias_dict(product_summary),
            "dados": {
                "product": product_summary,
                "guideTotal": self._host._total(root.get("guide")),
                "inspectionTotal": self._host._total(root.get("inspection")),
                "structureTotal": self._host._total(root.get("structure")),
            },
        }

    @staticmethod
    def _extract_product_detail_list(root: dict) -> list | None:
        detail_keys = (
            "prices", "stock", "purchases", "sales", "billing",
            "suppliers", "customers", "movements", "invoices",
            "open_orders", "items",
        )
        for key in detail_keys:
            value = root.get(key)
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value
        return None

    def _format_detail_preview_line(self, item: dict) -> str:
        parts: list[str] = []

        for key, value in list(item.items())[:8]:
            if value is None:
                continue

            label = self._host._humanize_key(key)

            if key in {
                "sale_price",
                "max_price",
                "discount_value",
                "last_price",
                "last_purchase_price",
                "standard_cost",
            }:
                parts.append(f"{label}: {self._host._format_currency(value)}")
            elif key == "discount_percent":
                parts.append(f"{label}: {self._host._format_num(value)}%")
            elif key in {
                "current_quantity",
                "available_quantity",
                "committed_quantity",
                "reserved_quantity",
                "lot_quantity",
            }:
                parts.append(f"{label}: {self._host._format_num(value)}")
            else:
                parts.append(f"{label}: {value}")

        return ", ".join(parts) if parts else "—"

    def _present_product_with_details(
        self, product_summary: dict, detail_list: list, root: dict
    ) -> dict:
        code = product_summary.get("code") or ""
        desc = product_summary.get("description") or ""

        linhas = [
            self._host._presenter_text(
                "productWithDetails",
                "introLine",
                code=str(code),
                description=str(desc),
            )
        ]

        for item in detail_list[:5]:
            preview = self._format_detail_preview_line(item)
            linhas.append(
                self._host._presenter_text(
                    "generic",
                    "collectionPreviewLine",
                    preview=preview,
                )
            )

        if len(detail_list) > 5:
            linhas.append(
                self._host._presenter_text(
                    "pagination",
                    "moreDetailRecords",
                    count=str(len(detail_list) - 5),
                )
            )

        all_keys = {}
        for item in detail_list:
            for k in item:
                if k not in all_keys:
                    all_keys[k] = True

        columns = [self._host._enrich_column(k, self._host._humanize_key(k)) for k in all_keys]
        rows = detail_list

        title = self._host._product_detail_title(code, root)

        return {
            "titulo": title,
            "linhas": linhas,
            "dados": {"product": product_summary, "items": rows},
            "apresentacao": {
                "type": "table",
                "title": title,
                "columns": columns,
                "rows": rows,
            },
        }
