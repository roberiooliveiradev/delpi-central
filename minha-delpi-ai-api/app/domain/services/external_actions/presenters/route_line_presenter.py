"""Formatadores de linha e helpers de coleção do ExternalActionResultPresenter — Fase 3A lote 14."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionRouteLinePresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _alias_dict(self, payload: dict) -> dict:
        return {
            self._host._humanize_key(key): value
            for key, value in payload.items()
            if value is not None
        }

    def _label_collection(self, key: str) -> str:
        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )

        labels = ChatProductOperationalContentService.get_mapping(
            "presenter",
            "collections",
            "labels",
        )

        return labels.get(key, key)

    def _total(self, value):
        if isinstance(value, dict):
            return value.get("total")

        return None

    def _collection_is_empty(self, value) -> bool:
        if not isinstance(value, dict):
            return True

        total = value.get("total")

        try:
            if total is not None and int(total) > 0:
                return False
        except (TypeError, ValueError):
            pass

        items = value.get("items")

        if isinstance(items, list) and items:
            return False

        data = value.get("data")

        if isinstance(data, list) and data:
            return False

        return True

    def _format_structure_component_line(
        self,
        code: str,
        description: str,
        item_type: str,
        quantity: object,
    ) -> str:
        separator = self._host._route_presentation("structureItems", "componentSeparator")
        parts = [
            self._host._route_presentation(
                "structureItems",
                "componentCode",
                code=code,
            )
        ]

        if description:
            parts.append(description)

        line = separator.join(parts[:2])

        if item_type:
            line += self._host._route_presentation(
                "structureItems",
                "componentType",
                type=item_type,
            )

        if quantity is not None:
            line += self._host._route_presentation(
                "structureItems",
                "componentQuantity",
                quantity=self._host._format_num(quantity),
            )

        return (
            self._host._route_presentation("structureItems", "componentBulletPrefix")
            + line
        )

    def _format_measurable_test_specs(self, test: dict) -> str | None:
        if not isinstance(test, dict):
            return None

        unit = str(test.get("unit") or "")
        spec_parts: list[str] = []
        nominal = test.get("nominal_value")
        lower = test.get("lower_spec_limit")
        upper = test.get("upper_spec_limit")
        missing = self._host._route_presentation("inspection", "missingLimit")

        if nominal is not None:
            spec_parts.append(
                self._host._route_presentation(
                    "inspection",
                    "specNominal",
                    nominal=str(nominal),
                    unit=unit,
                )
            )

        if lower is not None or upper is not None:
            spec_parts.append(
                self._host._route_presentation(
                    "inspection",
                    "specLimits",
                    lower=str(lower if lower is not None else missing),
                    upper=str(upper if upper is not None else missing),
                    unit=unit,
                )
            )

        return ", ".join(spec_parts) if spec_parts else None

    def _format_inspection_characteristic_line(self, item: dict) -> str | None:
        if not isinstance(item, dict):
            return None

        characteristic = str(
            item.get("characteristic")
            or item.get("specification")
            or item.get("step_description")
            or item.get("description")
            or "?"
        ).strip()
        inspection_type = str(item.get("inspection_type") or item.get("method") or "").strip()
        sequence = item.get("sequence")
        step = item.get("step")
        separator = self._host._route_presentation(
            "inspection",
            "characteristicPartsSeparator",
        )
        parts = [
            self._host._route_presentation(
                "inspection",
                "characteristicBold",
                characteristic=characteristic,
            )
        ]

        if inspection_type:
            parts.append(
                self._host._route_presentation(
                    "inspection",
                    "typeSuffix",
                    inspection_type=inspection_type,
                )
            )

        if sequence not in (None, ""):
            parts.append(
                self._host._route_presentation(
                    "inspection",
                    "sequenceSuffix",
                    sequence=str(sequence),
                )
            )
        elif step not in (None, ""):
            parts.append(
                self._host._route_presentation(
                    "inspection",
                    "sequenceSuffix",
                    sequence=str(step),
                )
            )

        return (
            self._host._route_presentation("inspection", "characteristicBulletPrefix")
            + separator.join(parts)
        )

    def _format_product_search_line(
        self,
        *,
        code: str,
        description: str,
        item_type: str,
        unit: str,
        quantity: object,
        level: object,
        is_hierarchy: bool,
    ) -> str:
        separator = self._host._route_presentation("productSearch", "separator")
        parts = [
            self._host._route_presentation("productSearch", "codeBold", code=code or "?")
        ]

        if description:
            parts.append(description)

        line = separator.join(parts[:2])

        if item_type:
            line += self._host._route_presentation(
                "productSearch",
                "typePart",
                type=item_type,
            )

        if unit:
            line += self._host._route_presentation(
                "productSearch",
                "unitPart",
                unit=unit,
            )

        if is_hierarchy:
            extras: list[str] = []

            if quantity is not None:
                extras.append(
                    self._host._route_presentation(
                        "productSearch",
                        "qtyExtra",
                        qty=str(quantity),
                    )
                )

            if level is not None:
                extras.append(
                    self._host._route_presentation(
                        "productSearch",
                        "levelExtra",
                        level=str(level),
                    )
                )

            if extras:
                line += self._host._route_presentation(
                    "productSearch",
                    "extrasSeparator",
                ) + ", ".join(extras)

        return line

    def _product_detail_scope(self, root: dict) -> str:
        if "prices" in root:
            return "prices"

        if "stock" in root:
            return "stock"

        if "purchases" in root:
            return "purchases"

        if "sales" in root or "billing" in root:
            return "sales"

        if "open_orders" in root:
            return "open_orders"

        return "default"

    def _product_detail_title(self, code: object, root: dict) -> str:
        scope = self._product_detail_scope(root)

        return self._host._presenter_text(
            "productDetailTitles",
            scope,
            code=str(code or "").strip(),
        )
