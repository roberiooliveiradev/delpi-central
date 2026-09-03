"""Reapresenta o último resultado operacional (tabela/gráfico/texto) sem nova rota errada."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_pagination_consolidation_service import (
    ChatPaginationConsolidationService,
)
from app.domain.services.chat_presentation_format_refinement_intent_service import (
    ChatPresentationFormatRefinementIntentService,
)
from app.domain.services.external_actions.external_action_sql_capability_service import (
    ExternalActionSqlCapabilityService,
)


class ChatPresentationFormatRefinementService:
    @classmethod
    def looks_like_format_refinement(cls, message: str | None) -> bool:
        return ChatPresentationFormatRefinementIntentService.looks_like_format_refinement(
            message,
        )

    @classmethod
    def detect_requested_format(cls, message: str) -> str | None:
        return ChatPresentationFormatRefinementIntentService.detect_requested_format(message)

    @classmethod
    def collect_last_successful_operation(
        cls,
        previous_messages: list[Any] | None,
        *,
        requested_format: str | None = None,
    ) -> dict[str, Any] | None:
        """Última operação reapresentável.

        Prefere ``compositionRole=primary`` (não enrichment wave-2) e, quando
        ``requested_format`` é informado, a tool que realmente carrega esse visual
        (ex.: tabela no estoque, não KPI escalar de vendas).
        """
        for item in reversed((previous_messages or [])[-16:]):
            metadata = cls._message_metadata(item)
            tool_calls = metadata.get("toolCalls") or []
            candidates: list[dict[str, Any]] = []

            for tool_call in tool_calls:
                operation = cls._operation_from_tool_call(tool_call)

                if operation:
                    candidates.append(operation)

            if not candidates:
                continue

            return cls._pick_best_operation(
                candidates,
                requested_format=requested_format,
            )

        return None

    @classmethod
    def _operation_from_tool_call(
        cls,
        tool_call: Any,
    ) -> dict[str, Any] | None:
        if not isinstance(tool_call, dict):
            return None

        if str(tool_call.get("name") or "") != "execute_external_action":
            return None

        tool_meta = tool_call.get("metadata") or {}

        if not isinstance(tool_meta, dict) or not tool_meta.get("ok"):
            return None

        path = str(tool_meta.get("path") or "").lower()
        entity = str(tool_meta.get("entity") or "").strip()

        if entity in {"protheus_table", "protheus_column"} or (
            not entity and "tables" in path and "/system/" in path
        ):
            return None

        arguments = tool_call.get("arguments") or {}
        parameters = arguments.get("parameters") or {}

        if not isinstance(parameters, dict):
            parameters = {}

        action_id = str(
            tool_meta.get("actionId") or arguments.get("actionId") or ""
        ).strip()

        if not action_id and not path:
            return None

        return {
            "actionId": action_id,
            "path": str(tool_meta.get("path") or ""),
            "parameters": dict(parameters),
            "metadata": dict(tool_meta),
            "arguments": dict(arguments) if isinstance(arguments, dict) else {},
        }

    @classmethod
    def _pick_best_operation(
        cls,
        candidates: list[dict[str, Any]],
        *,
        requested_format: str | None,
    ) -> dict[str, Any]:
        def sort_key(operation: dict[str, Any]) -> tuple[int, int, int]:
            meta = operation.get("metadata") or {}
            role = str(meta.get("compositionRole") or "").strip().lower()
            # primary primeiro; enrichment por último; sem role no meio.
            role_rank = 2 if role == "enrichment" else (0 if role == "primary" else 1)
            format_rank = -cls._format_capability_score(meta, requested_format)
            # Empate: preferir o primeiro da wave-1 (ordem original).
            return (role_rank, format_rank, 0)

        # Estável: índice original desempatar mantendo ordem da wave-1.
        indexed = list(enumerate(candidates))
        indexed.sort(
            key=lambda pair: (
                sort_key(pair[1])[0],
                sort_key(pair[1])[1],
                pair[0],
            )
        )
        return indexed[0][1]

    @classmethod
    def _format_capability_score(
        cls,
        meta: dict[str, Any],
        requested_format: str | None,
    ) -> int:
        fmt = str(requested_format or "").strip().lower()

        if not fmt:
            return 0

        preferred = str(meta.get("preferredFormat") or "").strip().lower()
        decision = meta.get("presentationDecision")
        selected = ""

        if isinstance(decision, dict):
            selected = str(decision.get("selected") or "").strip().lower()

        if fmt == "table":
            if cls._has_table_presentation(meta):
                return 100
            if preferred == "table" or selected == "table":
                return 60
            return 0

        if fmt == "kpi":
            if isinstance(meta.get("kpiPresentation"), dict):
                return 100
            if preferred == "kpi" or selected == "kpi":
                return 60
            return 0

        if fmt in {"chart", "line_chart", "bar_chart"}:
            if isinstance(meta.get("chartPresentation"), dict):
                return 100
            if preferred in {"chart", "line_chart"} or "chart" in selected:
                return 60
            return 0

        if fmt == "tree":
            if isinstance(meta.get("treePresentation"), dict):
                return 100
            if preferred == "tree" or selected == "tree":
                return 60
            return 0

        if preferred == fmt or selected == fmt:
            return 40

        return 0

    @classmethod
    def _has_table_presentation(cls, meta: dict[str, Any]) -> bool:
        table = meta.get("tablePresentation")

        if isinstance(table, dict) and str(table.get("type") or "").lower() == "table":
            rows = table.get("rows")
            return isinstance(rows, list) and len(rows) > 0

        bundled = meta.get("tablePresentations")

        if isinstance(bundled, list):
            for item in bundled:
                if (
                    isinstance(item, dict)
                    and str(item.get("type") or "").lower() == "table"
                    and isinstance(item.get("rows"), list)
                    and item.get("rows")
                ):
                    return True

        presentation = meta.get("presentation")

        return (
            isinstance(presentation, dict)
            and str(presentation.get("type") or "").lower() == "table"
            and isinstance(presentation.get("rows"), list)
            and bool(presentation.get("rows"))
        )

    @classmethod
    def resolve_payload(
        cls,
        previous_messages: list[Any] | None,
        *,
        operation: dict[str, Any],
    ) -> object | None:
        meta = operation.get("metadata") or {}

        # playbook_report / composite_analysis: tabela em cache não carrega summary —
        # força reconsulta HTTP para KPI/dashboard corretos.
        if cls._requires_live_envelope_refetch(meta):
            return None

        consolidation = meta.get("paginationConsolidation")

        if isinstance(consolidation, dict):
            consolidated = consolidation.get("consolidatedPayload")

            if isinstance(consolidated, dict) and consolidated.get("items"):
                return cls.wrap_payload_for_operation(operation, consolidated)

        cached = ChatPaginationConsolidationService.load_cached_payload(previous_messages)

        if isinstance(cached, dict) and cached.get("items"):
            return cls.wrap_payload_for_operation(operation, cached)

        for candidate in cls._iter_table_candidates(meta):
            if candidate.get("type") != "table":
                continue

            root = cls._rows_payload_from_table(candidate)

            if root:
                return cls.wrap_payload_for_operation(operation, root)

        return None

    @classmethod
    def _requires_live_envelope_refetch(cls, meta: dict[str, Any]) -> bool:
        api_meta = meta.get("apiDelpiResponseMeta")
        shape = ""

        if isinstance(api_meta, dict):
            shape = str(api_meta.get("shape") or "").strip().lower()

        if not shape:
            profile = meta.get("presentationProfile")
            if isinstance(profile, dict):
                shape = str(profile.get("openapiShape") or profile.get("shape") or "").strip().lower()

        return shape in {"playbook_report", "composite_analysis"}

    @classmethod
    def wrap_payload_for_operation(cls, operation: dict[str, Any], root: dict[str, Any]) -> dict[str, Any]:
        path = str(operation.get("path") or "").lower()
        items = root.get("items")
        rows = root.get("rows")

        if cls._is_sql_operation(operation):
            if ExternalActionSqlCapabilityService.is_sql_result_payload(root):
                return {"data": root}

            if isinstance(rows, list):
                return {"data": root}

            if isinstance(items, list):
                return {
                    "data": {
                        "rows": items,
                        "total": root.get("total", len(items)),
                    }
                }

            return {"data": root}

        if not isinstance(items, list):
            return {"data": root}

        payload_root = dict(root)
        metadata = operation.get("metadata") if isinstance(operation.get("metadata"), dict) else {}
        entity = str(metadata.get("entity") or "").strip()

        if not entity:
            from app.domain.services.chat_operational_response_profile_service import (
                ChatOperationalResponseProfileService,
            )

            entity = str(
                ChatOperationalResponseProfileService.resolve_entity(path=path) or ""
            ).strip()

        if entity == "product_stock":
            return {"data": {"stock": payload_root}}

        return {"data": payload_root}

    @classmethod
    def _is_sql_operation(cls, operation: dict[str, Any]) -> bool:
        meta = operation.get("metadata") or {}

        return ExternalActionSqlCapabilityService.is_sql_execution_context(
            path=str(operation.get("path") or ""),
            operation_id=str(meta.get("operationId") or ""),
            action_id=str(operation.get("actionId") or ""),
            sensitivity=str(meta.get("sensitivity") or ""),
        )

    @classmethod
    def rebuild_metadata_for_refinement(
        cls,
        *,
        external_use_case,
        operation: dict[str, Any],
        payload: object,
        requested_format: str | None,
        user_message: str | None,
    ) -> dict[str, Any] | None:
        action_id = str(operation.get("actionId") or "").strip()

        if not action_id or payload is None or external_use_case is None:
            return None

        parameters = dict(operation.get("parameters") or {})

        if requested_format:
            parameters["sessionResponseFormat"] = requested_format

        if user_message:
            parameters["userMessage"] = user_message

        try:
            rebuilt = external_use_case.build_metadata_for_data(
                action_id=action_id,
                data=payload,
                parameters=parameters,
            )
        except ValueError:
            return None

        prior = operation.get("metadata") or {}

        for key in (
            "ok",
            "statusCode",
            "actionId",
            "path",
            "provider",
            "method",
            "operationId",
            "apiDelpiResponseMeta",
        ):
            if key in prior:
                rebuilt[key] = prior[key]

        consolidation = prior.get("paginationConsolidation")

        if isinstance(consolidation, dict):
            rebuilt["paginationConsolidation"] = dict(consolidation)

        return rebuilt

    @classmethod
    def _iter_table_candidates(cls, meta: dict[str, Any]):
        for key in ("tablePresentation", "presentation", "chartPresentation"):
            candidate = meta.get(key)

            if isinstance(candidate, dict):
                yield candidate

        bulk = meta.get("tablePresentations")

        if isinstance(bulk, list):
            for candidate in reversed(bulk):
                if isinstance(candidate, dict):
                    yield candidate

    @classmethod
    def _rows_payload_from_table(cls, table: dict[str, Any]) -> dict[str, Any] | None:
        rows = table.get("rows")

        if not isinstance(rows, list) or not rows:
            return None

        return {
            "items": rows,
            "total": len(rows),
            "page": 1,
            "page_size": len(rows),
            "total_pages": 1,
        }

    @staticmethod
    def _message_metadata(item: Any) -> dict[str, Any]:
        if hasattr(item, "metadata"):
            metadata = getattr(item, "metadata", None)

            return metadata if isinstance(metadata, dict) else {}

        if isinstance(item, dict):
            metadata = item.get("metadata")

            return metadata if isinstance(metadata, dict) else {}

        return {}
