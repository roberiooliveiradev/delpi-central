"""Catálogo OpenAPI de produto — lookup e parâmetros (DOCIE Fase 4)."""

from __future__ import annotations

import re
from typing import Callable

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_refinement_service import (
    ChatOperationalRefinementService,
)
from app.domain.services.chat_product_operational_content_service import (
    ChatProductOperationalContentService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ExternalActionProductRouteCatalogService:
    HIERARCHICAL_PRODUCT_MAX_DEPTH = 15

    @staticmethod
    def filter_parameters_to_schema(action: dict, parameters: dict | None) -> dict:
        """Mantém só chaves declaradas no OpenAPI da action."""
        allowed = {
            str(parameter.get("name"))
            for parameter in (action.get("parametersSchema") or [])
            if parameter.get("name")
        }

        if not allowed:
            return {}

        return {
            key: value
            for key, value in (parameters or {}).items()
            if key in allowed
        }

    @staticmethod
    def is_product_sales_summary_path(path: str) -> bool:
        lowered = str(path or "").lower().rstrip("/")

        if "open-orders" in lowered or "/billing" in lowered:
            return False

        return lowered.endswith("/sales") and "/products/" in lowered

    def __init__(self, repository) -> None:
        self.repository = repository

    def find_allowed_actions_by_markers(
        self,
        *,
        path_markers: list[str],
        operation_markers: list[str],
        allowed_action_ids: list[str],
        method: str = "GET",
    ) -> list[dict]:
        """Resolve actions autorizadas pelo catálogo — não depende de ranking semântico."""
        allowed = {str(item) for item in allowed_action_ids if str(item).strip()}

        if not allowed or (not path_markers and not operation_markers):
            return []

        list_actions = getattr(self.repository, "list_actions", None)

        if not callable(list_actions):
            return []

        matches: list[dict] = []

        for action in list_actions():
            if str(action.get("actionId") or "") not in allowed:
                continue

            if str(action.get("method") or "").upper() != method.upper():
                continue

            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()

            if path_markers and not any(marker in path for marker in path_markers):
                continue

            if operation_markers and not any(
                marker in operation_id for marker in operation_markers
            ):
                if path_markers:
                    continue

            if not path_markers and operation_markers and not any(
                marker in operation_id for marker in operation_markers
            ):
                continue

            matches.append(action)

        return matches


    def load_candidates(
        self,
        message: str,
        *,
        allowed_action_ids: list[str],
        candidates_loader: Callable | None = None,
    ) -> list[dict]:
        candidates: list[dict] = []

        if allowed_action_ids and candidates_loader:
            candidates = candidates_loader(
                message,
                allowed_action_ids=allowed_action_ids,
                limit=80,
            )

        if not candidates:
            candidates = self.repository.find_candidate_actions(
                message,
                limit=80,
            )

        return candidates or []

    @staticmethod
    def stable_sort_by_allowed_action_ids(
        candidates: list[dict],
        allowed_action_ids: list[str],
    ) -> list[dict]:
        order = {
            str(action_id): index
            for index, action_id in enumerate(allowed_action_ids or [])
            if str(action_id).strip()
        }

        return sorted(
            candidates,
            key=lambda action: order.get(str(action.get("actionId") or ""), 999),
        )

    @classmethod
    def clamp_max_depth_for_path(cls, value: int, path: str) -> int:
        try:
            depth = int(value)
        except (TypeError, ValueError):
            depth = 10

        lowered = str(path or "").lower()
        cap = (
            ExternalActionProductRouteCatalogService.HIERARCHICAL_PRODUCT_MAX_DEPTH
            if "/structure" in lowered or "/parents" in lowered
            else 99
        )

        return min(max(depth, 1), cap)


    @classmethod
    def is_drawing_analyser_request(
        cls,
        message: str | None,
        path: str,
        *,
        attachment_ids: list | None = None,
        drawing_analysis_mode: bool = False,
    ) -> bool:
        if "/analyser" not in str(path or "").lower():
            return False

        from app.domain.services.chat_drawing_analyser_parameter_service import (
            ChatDrawingAnalyserParameterService,
        )

        return ChatDrawingAnalyserParameterService.requires_full_view(
            drawing_analysis_mode=drawing_analysis_mode,
            message=message,
            attachment_ids=attachment_ids,
        )


    def build_product_parameters(
        self,
        action: dict,
        code: str,
        *,
        message: str | None = None,
        previous_messages: list | None = None,
        drawing_analysis_mode: bool = False,
        attachment_ids: list | None = None,
    ) -> dict:
        parameters = {}
        path = (action.get("path") or "").lower()
        is_full_listing = "/structure" in path or "/parents" in path
        normalized = (
            ChatMessageNormalizationService.normalize_for_matching(message)
            if message
            else ""
        )

        branch_code = (
            ChatOperationalRefinementService.extract_branch_code(normalized)
            if normalized
            else None
        )
        warehouse_code = (
            ChatOperationalRefinementService.extract_warehouse_code(normalized)
            if normalized
            else None
        )
        requested_page_size = (
            ChatOperationalRefinementService.extract_requested_page_size(normalized)
            if normalized
            else None
        )
        requested_page = (
            ChatOperationalRefinementService.extract_requested_page(normalized)
            if normalized
            else None
        )

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")

            if not name:
                continue

            lowered = name.lower()

            if lowered in {
                "code",
                "product_code",
                "productcode",
                "codigo",
                "cod_produto",
                "produto",
                "item",
                "id",
                "identifier",
                "referencia",
                "referência",
                "customer_reference",
                "delpi_code",
            }:
                parameters[name] = code

            elif lowered in {
                "query",
                "q",
                "search",
                "description",
                "descricao",
                "term",
            }:
                parameters[name] = code

            elif lowered == "page":
                parameters[name] = requested_page or 1

            elif lowered in {"page_size", "pagesize", "limit"}:
                if requested_page_size is not None:
                    parameters[name] = requested_page_size
                elif self.is_drawing_analyser_request(
                    message,
                    path,
                    attachment_ids=attachment_ids,
                    drawing_analysis_mode=drawing_analysis_mode,
                ):
                    parameters[name] = 50
                else:
                    parameters[name] = 200 if is_full_listing else 50

            elif lowered in {"max_depth", "maxdepth", "depth", "nivel", "levels"}:
                if self.is_drawing_analyser_request(
                    message,
                    path,
                    attachment_ids=attachment_ids,
                    drawing_analysis_mode=drawing_analysis_mode,
                ):
                    parameters[name] = 10
                else:
                    parameters[name] = (
                        self.HIERARCHICAL_PRODUCT_MAX_DEPTH
                        if is_full_listing
                        else min(10, self.HIERARCHICAL_PRODUCT_MAX_DEPTH)
                    )

            elif lowered in {"branch", "filial", "branch_code", "branchcode"} and branch_code:
                parameters[name] = branch_code

            elif lowered in {
                "warehouse",
                "armazem",
                "armazém",
                "warehouse_code",
                "deposito",
                "depósito",
                "location",
                "local",
            } and warehouse_code:
                parameters[name] = warehouse_code

            elif lowered == "view" and "/analyser" in path:
                from app.domain.services.chat_product_query_intent_service import (
                    ChatProductQueryIntentService,
                )

                if self.is_drawing_analyser_request(
                    message,
                    path,
                    attachment_ids=attachment_ids,
                    drawing_analysis_mode=drawing_analysis_mode,
                ):
                    parameters[name] = "full"
                    continue

                normalized_message = (
                    ChatMessageNormalizationService.normalize_for_matching(message)
                    if message
                    else ""
                )
                if ChatProductQueryIntentService._looks_like_full_analyser_question(
                    normalized_message
                ):
                    parameters[name] = "full"
                else:
                    parameters[name] = "summary"

            elif lowered == "adjustment_percent":
                percent = self.extract_adjustment_percent(normalized)

                if percent is not None:
                    parameters[name] = percent

            elif lowered == "top_n":
                top_n = self.extract_top_n(normalized)

                if top_n is not None:
                    parameters[name] = top_n

            elif lowered == "price_source":
                last_purchase_terms = ChatProductOperationalContentService.list(
                    "priceSourceDetection",
                    "lastPurchaseTerms",
                )
                standard_cost_terms = ChatProductOperationalContentService.list(
                    "priceSourceDetection",
                    "standardCostTerms",
                )

                if any(term in normalized for term in last_purchase_terms):
                    parameters[name] = "last_purchase"
                elif any(term in normalized for term in standard_cost_terms):
                    parameters[name] = "standard_cost"

        from app.domain.services.chat_operational_date_parameter_service import (
            ChatOperationalDateParameterService,
        )
        from app.domain.services.chat_drawing_analyser_parameter_service import (
            ChatDrawingAnalyserParameterService,
        )

        parameters = ChatOperationalDateParameterService.merge_into_parameters(
            action,
            message,
            parameters,
            previous_messages=previous_messages,
        )

        return ChatDrawingAnalyserParameterService.apply_to_parameters(
            parameters,
            action=action,
            drawing_analysis_mode=drawing_analysis_mode,
            message=message,
            attachment_ids=attachment_ids,
        )


    @staticmethod
    def extract_adjustment_percent(normalized: str) -> float | None:
        if not normalized:
            return None

        patterns = (
            r"(?:aumento|reajuste|subir|simul\w*)\s*(?:de\s*)?([+-]?\d+(?:[.,]\d+)?)\s*(?:%|percento|por\s*cento)",
            r"([+-]?\d+(?:[.,]\d+)?)\s*(?:%|percento|por\s*cento)\s*(?:de\s*)?(?:aumento|reajuste|simul)",
        )

        for pattern in patterns:
            match = re.search(pattern, normalized)

            if match:
                try:
                    return float(match.group(1).replace(",", "."))
                except ValueError:
                    return None

        return None


    def build_exclusive_catalog_parameters(
        self,
        action: dict,
        *,
        message: str,
        normalized: str,
    ) -> dict:
        parameters: dict = {}
        requested_page_size = ChatOperationalRefinementService.extract_requested_page_size(
            normalized
        )
        requested_page = ChatOperationalRefinementService.extract_requested_page(normalized)
        product_code = ChatProductQueryIntentService.extract_product_code(message or "")

        finished_product_markers = (
            "produto",
            "produtos",
            " pa ",
            " pas ",
            "acabado",
            "acabados",
        )
        default_view = (
            "by_finished_product"
            if any(marker in normalized for marker in finished_product_markers)
            else "by_material"
        )

        for parameter in action.get("parametersSchema") or []:
            name = parameter.get("name")
            if not name:
                continue

            lowered = name.lower()

            if lowered == "view":
                parameters[name] = default_view
            elif lowered == "limit":
                parameters[name] = requested_page_size or 10
            elif lowered == "offset":
                page = requested_page or 1
                page_size = requested_page_size or 10
                parameters[name] = (page - 1) * page_size
            elif lowered in {"finished_product_code", "finishedproductcode"} and product_code:
                parameters[name] = product_code
            elif lowered in {"raw_material_code", "rawmaterialcode"} and product_code:
                parameters[name] = product_code
            elif lowered in {"max_depth", "maxdepth"}:
                parameters[name] = self.HIERARCHICAL_PRODUCT_MAX_DEPTH

        if "view" not in {key.lower() for key in parameters}:
            parameters["view"] = default_view

        return self.filter_parameters_to_schema(action, parameters)


    @staticmethod
    def extract_top_n(normalized: str) -> int | None:
        if not normalized:
            return None

        patterns = (
            r"\btop\s*(\d+)\b",
            r"\b(\d+)\s*(?:principais|maiores|primeir)",
        )

        for pattern in patterns:
            match = re.search(pattern, normalized)

            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    return None

        return None
