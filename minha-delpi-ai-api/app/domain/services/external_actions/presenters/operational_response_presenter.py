"""Respostas operacionais vazias, erros API e normalização — Fase 3A lote 15."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from app.domain.services.chat_operational_response_profile_service import (
    ChatOperationalResponseProfileService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionOperationalResponsePresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _fallback_title(self, path: str) -> str | None:
        if not path:
            return None

        lowered = path.lower()
        triggers = (
            "dashboard",
            "/commercial/",
            "/financial/",
            "/finacial/",
            "/production/",
            "/hr/",
            "/quality/",
        )

        if not any(fragment in lowered for fragment in triggers):
            return None

        return self._host._kpi_title(path)

    def _present_dict_fallback(self, root: dict, path: str) -> dict | None:
        if not root:
            return None

        linhas = []
        title = self._fallback_title(path) or self._host._presenter_text(
            "generic", "queryResultTitle"
        )

        for key, value in root.items():
            if isinstance(value, dict):
                sub_items = [
                    self._host._presenter_text(
                        "generic",
                        "dictNestedValue",
                        key=str(nested_key),
                        value=str(nested_value),
                    )
                    for nested_key, nested_value in value.items()
                ]
                linhas.append(
                    self._host._presenter_text(
                        "generic",
                        "dictNestedLine",
                        label=self._host._humanize_key(key),
                        items=", ".join(sub_items),
                    )
                )
            elif isinstance(value, list) and value:
                linhas.append(
                    self._host._presenter_text(
                        "generic",
                        "dictListItems",
                        label=self._host._humanize_key(key),
                        count=str(len(value)),
                    )
                )
            elif value is not None:
                linhas.append(
                    self._host._presenter_text(
                        "generic",
                        "dictScalarLine",
                        label=self._host._humanize_key(key),
                        value=self._host._format_field_value(key, value),
                    )
                )

        if linhas:
            return {
                "titulo": title,
                "linhas": linhas[:12],
                "dados": root,
            }

        return None

    @staticmethod
    def _extract_product_code_from_path(path: str) -> str:
        match = re.search(r"/products/(\d+)/", str(path or ""), flags=re.IGNORECASE)

        if match:
            return match.group(1)

        return ""

    def _present_empty_operational_result(self, *, path: str, root) -> dict | None:
        entity = ChatOperationalResponseProfileService.resolve_entity(path=path)

        if not (
            ChatOperationalResponseProfileService.is_product_operational_entity(entity)
            or self._legacy_is_product_operational_path(path)
        ):
            return None

        if not self._is_empty_operational_payload(root):
            return None

        product_code = self._extract_product_code_from_path(path)
        route_key = ChatOperationalResponseProfileService.operational_empty_route_key(
            entity
        ) or self._legacy_operational_empty_route_key(path)

        if route_key and product_code:
            linha = self._host._presenter_text(
                "operationalEmpty", route_key, code=product_code
            )
        elif route_key:
            linha = self._host._presenter_text("operationalEmpty", f"{route_key}Generic")
        else:
            linha = self._host._presenter_text("operationalEmpty", "default")

        titulo = self._host._infer_items_title([], path) or self._host._presenter_text(
            "generic", "defaultQueryTitle"
        )

        return {
            "titulo": titulo,
            "linhas": [linha],
            "dados": {
                "items": [],
                "total": 0,
                "product_code": product_code or None,
            },
        }

    @staticmethod
    def _is_empty_operational_payload(root) -> bool:
        if isinstance(root, list):
            return len(root) == 0

        if not isinstance(root, dict):
            return False

        total = root.get("total")

        if total == 0:
            return True

        items = root.get("items")

        if isinstance(items, list) and not items:
            return True

        nested = root.get("data")

        if isinstance(nested, list) and not nested:
            return True

        if isinstance(nested, dict) and nested.get("total") == 0:
            inner = nested.get("data") or nested.get("items")

            if inner is None or inner == []:
                return True

        return False

    @staticmethod
    def _legacy_operational_empty_route_key(path: str) -> str | None:
        lowered_path = str(path or "").lower()

        if "/suppliers" in lowered_path:
            return "suppliers"

        if "/customers" in lowered_path:
            return "customers"

        if "/stock" in lowered_path:
            return "stock"

        if "/structure" in lowered_path:
            return "structure"

        if "/parents" in lowered_path:
            return "parents"

        if "/guide" in lowered_path:
            return "guide"

        if "/inspection" in lowered_path:
            return "inspection"

        if "/sales" in lowered_path or "/purchases" in lowered_path:
            return "salesPurchases"

        return None

    @staticmethod
    def _is_product_operational_path(path: str) -> bool:
        return ChatOperationalResponseProfileService.is_product_operational_path(path)

    @staticmethod
    def _legacy_is_product_operational_path(path: str) -> bool:
        lowered = str(path or "").lower()

        return any(
            segment in lowered
            for segment in (
                "/guide",
                "/inspection",
                "/stock",
                "/structure",
                "/parents",
                "/purchases",
                "/sales",
                "/suppliers",
                "/customers",
            )
        )

    @staticmethod
    def _format_protheus_date(value) -> str | None:
        raw = str(value or "").strip()

        if len(raw) != 8 or not raw.isdigit():
            return raw or None

        return f"{raw[6:8]}/{raw[4:6]}/{raw[0:4]}"

    @staticmethod
    def _format_currency(value) -> str:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)

        formatted = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        return formatted

    def _detect_api_error(self, data, *, path: str = "") -> dict | None:
        if not isinstance(data, dict):
            return None

        detail = data.get("detail") or data.get("error") or data.get("message")
        status = data.get("status_code") or data.get("status")

        is_error_detail = isinstance(detail, str) and detail.lower() in (
            "not found", "unauthorized", "forbidden", "internal server error",
            "bad request", "service unavailable",
        )

        is_error_status = isinstance(status, int) and status >= 400

        if not is_error_detail and not is_error_status:
            if isinstance(data.get("success"), bool) and not data["success"]:
                from app.domain.services.chat_sql_execution_error_interpretation_service import (
                    ChatSqlExecutionErrorInterpretationService,
                )

                raw_msg = str(
                    data.get("message")
                    or self._host._presenter_text("apiErrors", "unknown")
                )
                friendly = ChatSqlExecutionErrorInterpretationService.user_facing_message(
                    raw_msg,
                    path=path,
                )
                msg = friendly or raw_msg

                if ChatSqlExecutionErrorInterpretationService.is_raw_driver_dump(raw_msg):
                    msg = friendly or self._host._analyser_markdown("sqlEnvironmentFailed")

                return {
                    "titulo": self._host._presenter_text("generic", "queryErrorTitle"),
                    "linhas": [msg],
                    "dados": None,
                }
            return None

        if isinstance(detail, str):
            error_key_map = {
                "not found": "notFound",
                "unauthorized": "unauthorized",
                "forbidden": "forbidden",
            }
            mapped = error_key_map.get(detail.lower())
            msg = (
                self._host._presenter_text("apiErrors", mapped)
                if mapped
                else self._host._presenter_text("apiErrors", "withDetail", detail=detail)
            )
        else:
            msg = self._host._presenter_text("apiErrors", "withStatus", status=str(status))

        return {
            "titulo": self._host._presenter_text("generic", "queryErrorTitle"),
            "linhas": [msg],
            "dados": None,
        }

    @staticmethod
    def _unwrap_data(data):
        root = data

        if isinstance(root, dict) and "data" in root:
            root = root["data"]

        if isinstance(root, dict) and "data" in root:
            root = root["data"]

        return root

    def _normalize_api_section(self, block, *, _depth: int = 0):
        """Desembrulha blocos `{ success, data }` retornados pela API DELPI."""
        if not isinstance(block, dict):
            return block

        inner = block.get("data")

        if inner is None and "success" not in block and "total" not in block:
            return block

        if isinstance(inner, list):
            normalized: dict = {"items": inner}
            total = block.get("total")

            if total is not None:
                normalized["total"] = total

            return normalized

        if isinstance(inner, dict):
            merged = dict(inner)

            for key in ("total", "page", "page_size", "total_pages", "filters", "success"):
                if key in block and key not in merged:
                    merged[key] = block[key]

            if "components" in merged and "items" not in merged:
                components = merged.get("components")

                if isinstance(components, list):
                    merged["items"] = components

            if merged.get("code") and "root" not in merged:
                merged.setdefault(
                    "root",
                    {
                        "code": merged.get("code"),
                        "description": merged.get("description"),
                        "type": merged.get("type"),
                        "unit": merged.get("unit"),
                        "quantity": merged.get("quantity", 1),
                    },
                )

            if (
                _depth < 4
                and isinstance(merged.get("data"), dict)
                and not str(merged.get("code") or "").strip()
            ):
                return self._normalize_api_section(merged, _depth=_depth + 1)

            return merged

        return block
