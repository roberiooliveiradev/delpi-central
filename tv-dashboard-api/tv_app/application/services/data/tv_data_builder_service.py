"""Assistente de dados TV — turn determinístico + materialize para o slide."""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from tv_app.application.services.data.tv_data_builder_content_service import (
    TvDataBuilderContentService,
)
from tv_app.application.services.data.tv_data_builder_draft import (
    add_source,
    empty_draft,
    find_source,
    propose_join,
    remove_source,
    set_columns,
    set_params,
)
from tv_app.application.services.data.tv_data_builder_session_store import (
    SESSION_STORE,
    TvDataBuilderSessionStore,
)
from tv_app.application.services.data.tv_data_param_defaults_service import (
    apply_catalog_param_defaults,
)
from tv_app.application.services.data.tv_data_route_suggest_service import (
    TvDataRouteSuggestService,
)
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService

logger = logging.getLogger(__name__)


def _msg(
    role: str,
    text: str,
    *,
    suggestions: list[dict[str, Any]] | None = None,
    tool: str | None = None,
) -> dict[str, Any]:
    return {
        "id": uuid.uuid4().hex[:12],
        "role": role,
        "text": text,
        "suggestions": suggestions or [],
        "tool": tool,
    }


class TvDataBuilderService:
    def __init__(
        self,
        catalog: TvDataRouteCatalogService | None = None,
        *,
        store: TvDataBuilderSessionStore | None = None,
        suggest: TvDataRouteSuggestService | None = None,
    ) -> None:
        self._catalog = catalog or TvDataRouteCatalogService()
        self._store = store or SESSION_STORE
        self._suggest = suggest or TvDataRouteSuggestService(self._catalog)

    def create_session(self) -> dict[str, Any]:
        return self._store.create()

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        return self._store.get(session_id)

    def turn(
        self,
        session_id: str,
        *,
        message: str | None = None,
        action: dict[str, Any] | None = None,
        authorization: str | None = None,
        user: Any = None,
    ) -> dict[str, Any] | None:
        preview_requested = False

        def mutator(payload: dict[str, Any]) -> dict[str, Any]:
            nonlocal preview_requested
            draft = dict(payload.get("draft") or empty_draft())
            messages = list(payload.get("messages") or [])
            preview = payload.get("preview")

            if action and isinstance(action, dict):
                kind = str(action.get("type") or action.get("action") or "").strip()
                if kind == "preview":
                    preview_requested = True
                    messages.append(
                        _msg(
                            "assistant",
                            TvDataBuilderContentService.message("previewRequested"),
                            tool="preview",
                        )
                    )
                else:
                    draft, new_messages, preview = self._apply_action(draft, action, preview)
                    messages.extend(new_messages)
            else:
                text = str(message or "").strip()
                if text:
                    messages.append(_msg("user", text))
                    if TvDataBuilderContentService.matches("preview", text):
                        preview_requested = True
                        messages.append(
                            _msg(
                                "assistant",
                                TvDataBuilderContentService.message("previewRequested"),
                                tool="preview",
                            )
                        )
                    else:
                        draft, new_messages, preview = self._interpret(text, draft, preview)
                        messages.extend(new_messages)

            return {
                **payload,
                "draft": draft,
                "messages": messages[-80:],
                "preview": preview,
            }

        updated = self._store.update(session_id, mutator)
        if updated is None:
            return None
        if not preview_requested:
            return updated

        preview_result = self.preview(
            session_id,
            authorization=authorization,
            user=user,
        )
        if isinstance(preview_result, dict) and preview_result.get("session"):
            return preview_result["session"]
        if isinstance(preview_result, dict) and not preview_result.get("ok"):

            def err_mutator(payload: dict[str, Any]) -> dict[str, Any]:
                messages = list(payload.get("messages") or [])
                messages.append(
                    _msg(
                        "assistant",
                        str(
                            preview_result.get("message")
                            or TvDataBuilderContentService.message("previewEmpty")
                        ),
                        tool="preview",
                    )
                )
                return {**payload, "messages": messages[-80:]}

            return self._store.update(session_id, err_mutator) or updated
        return updated

    def materialize(self, session_id: str) -> dict[str, Any] | None:
        session = self._store.get(session_id)
        if not session:
            return None
        draft = session.get("draft") or empty_draft()
        sources = [s for s in (draft.get("sources") or []) if isinstance(s, dict)]
        if not sources:
            return {
                "ok": False,
                "message": TvDataBuilderContentService.message("materializeEmpty"),
                "blocks": [],
                "draft": draft,
            }

        primary = str(draft.get("primaryLocalId") or sources[0].get("localId") or "")
        transform = draft.get("transform")
        blocks: list[dict[str, Any]] = []
        for source in sources:
            local_id = str(source.get("localId") or "")
            block: dict[str, Any] = {
                "type": "data_source",
                "localId": local_id,
                "queryName": source.get("queryName"),
                "dataBinding": {
                    "operationId": source.get("operationId"),
                    "params": dict(source.get("params") or {}),
                    "displayMode": "auto",
                    "label": source.get("label"),
                },
            }
            if local_id == primary and isinstance(transform, dict) and transform.get("steps"):
                # Merge steps referenciam localId do draft; no slide o MFE remapeará
                # sourceId → id real do bloco após criar todos.
                block["dataTransform"] = transform
                block["isPrimary"] = True
            else:
                block["isPrimary"] = local_id == primary
            blocks.append(block)

        return {
            "ok": True,
            "blocks": blocks,
            "primaryLocalId": primary,
            "draft": draft,
            "preferredView": "table",
        }

    def preview(
        self,
        session_id: str,
        *,
        authorization: str | None = None,
        user: Any = None,
    ) -> dict[str, Any] | None:
        """Força prévia tabular do rascunho (fonte âncora + transform)."""
        session = self._store.get(session_id)
        if not session:
            return None
        draft = session.get("draft") or empty_draft()
        sources = [s for s in (draft.get("sources") or []) if isinstance(s, dict)]
        if not sources:
            return {
                "ok": False,
                "message": TvDataBuilderContentService.message("previewEmpty"),
                "preview": None,
                "draft": draft,
            }

        primary = str(draft.get("primaryLocalId") or sources[0].get("localId") or "")
        transform = draft.get("transform")
        sibling_blocks: list[dict[str, Any]] = []
        primary_block: dict[str, Any] | None = None
        for source in sources:
            local_id = str(source.get("localId") or "")
            block: dict[str, Any] = {
                "id": local_id,
                "type": "data_source",
                "queryName": source.get("queryName"),
                "dataBinding": {
                    "operationId": source.get("operationId"),
                    "params": dict(source.get("params") or {}),
                    "displayMode": "auto",
                    "label": source.get("label"),
                },
            }
            if local_id == primary and isinstance(transform, dict) and transform.get("steps"):
                # Remap merge sourceId já é localId do draft (= id do bloco temporário).
                block["dataTransform"] = transform
            sibling_blocks.append(block)
            if local_id == primary:
                primary_block = block

        if primary_block is None:
            primary_block = sibling_blocks[0]

        from tv_app.application.services.data.tv_data_preview_service import TvDataPreviewService

        try:
            selected = TvDataPreviewService(self._catalog).preview_block(
                primary_block,
                native_config={"blocks": sibling_blocks},
                authorization=authorization,
                user=user,
                force_refresh=True,
                preview_options={"maxRows": 20, "includeColumnProfile": False},
            )
            table = self._extract_preview_table(selected)
            preview_payload = {
                "columns": table.get("columns") or [],
                "rows": table.get("rows") or [],
                "rowCount": table.get("rowCount") or 0,
            }
            ok_message = (
                TvDataBuilderContentService.message("previewOk")
                if preview_payload["columns"] or preview_payload["rowCount"]
                else TvDataBuilderContentService.message("previewEmptyResult")
            )

            def mutator(payload: dict[str, Any]) -> dict[str, Any]:
                messages = list(payload.get("messages") or [])
                messages.append(
                    _msg(
                        "assistant",
                        ok_message,
                        tool="preview",
                    )
                )
                return {
                    **payload,
                    "messages": messages[-80:],
                    "preview": preview_payload,
                }

            updated = self._store.update(session_id, mutator)
            return {
                "ok": True,
                "preview": preview_payload,
                "session": updated,
                "draft": (updated or {}).get("draft") or draft,
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("builder preview failed: %s", exc)
            return {
                "ok": False,
                "message": TvDataBuilderContentService.message(
                    "previewFailed", error=str(exc)[:200]
                ),
                "preview": session.get("preview"),
                "draft": draft,
            }

    @staticmethod
    def _extract_preview_table(selected: dict[str, Any] | Any) -> dict[str, Any]:
        if not isinstance(selected, dict):
            return {"columns": [], "rows": [], "rowCount": 0}
        resolved = selected.get("resolved") if isinstance(selected.get("resolved"), dict) else {}
        query = resolved.get("query") if isinstance(resolved.get("query"), dict) else {}
        table = resolved.get("table") if isinstance(resolved.get("table"), dict) else {}
        preview = resolved.get("preview") if isinstance(resolved.get("preview"), dict) else {}

        raw_rows = (
            preview.get("rows")
            or table.get("rows")
            or query.get("rows")
            or query.get("items")
            or selected.get("rows")
            or []
        )
        if not isinstance(raw_rows, list):
            raw_rows = []

        columns: list[str] = []
        for candidate in (
            preview.get("columns"),
            table.get("columns"),
            query.get("columns"),
        ):
            if isinstance(candidate, list) and candidate:
                columns = [
                    str(item.get("key") if isinstance(item, dict) else item)
                    for item in candidate
                    if item is not None
                ]
                break
        if not columns and raw_rows and isinstance(raw_rows[0], dict):
            columns = [str(k) for k in raw_rows[0].keys()]

        rows: list[list[Any]] = []
        for row in raw_rows[:20]:
            if isinstance(row, dict):
                rows.append([row.get(col) for col in columns] if columns else list(row.values()))
            elif isinstance(row, list):
                rows.append(row)
        return {"columns": columns, "rows": rows, "rowCount": len(raw_rows)}

    def _apply_action(
        self,
        draft: dict[str, Any],
        action: dict[str, Any],
        preview: Any,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], Any]:
        kind = str(action.get("type") or action.get("action") or "").strip()
        messages: list[dict[str, Any]] = []

        if kind == "add_source":
            params = action.get("params") if isinstance(action.get("params"), dict) else None
            return self._tool_add_source(
                draft,
                str(action.get("operationId") or ""),
                preview,
                params=params,
            )
        if kind == "remove_source":
            return self._tool_remove_source(
                draft,
                local_id=str(action.get("localId") or "") or None,
                operation_id=str(action.get("operationId") or "") or None,
                preview=preview,
            )
        if kind == "set_params":
            params = action.get("params") if isinstance(action.get("params"), dict) else {}
            return self._tool_set_params(
                draft,
                params,
                local_id=str(action.get("localId") or "") or None,
                preview=preview,
            )
        if kind == "set_columns":
            cols = action.get("columns") if isinstance(action.get("columns"), list) else []
            return self._tool_set_columns(draft, [str(c) for c in cols], preview)
        if kind == "propose_join":
            return self._tool_propose_join(
                draft,
                left_key=str(action.get("leftKey") or "op"),
                right_key=str(action.get("rightKey") or "") or None,
                preview=preview,
            )
        if kind == "mark_ready":
            return self._tool_mark_ready(draft, preview)
        if kind == "suggest_sources":
            query = str(action.get("query") or "").strip()
            return self._tool_suggest(draft, query, preview)

        messages.append(
            _msg("assistant", TvDataBuilderContentService.message("unknownCommand"), tool=kind or "unknown")
        )
        return draft, messages, preview

    def _interpret(
        self,
        text: str,
        draft: dict[str, Any],
        preview: Any,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], Any]:
        content = TvDataBuilderContentService

        if content.matches("markReady", text):
            return self._tool_mark_ready(draft, preview)

        if content.matches("removeSource", text):
            return self._tool_remove_source(draft, operation_id=text, preview=preview)

        if content.matches("proposeJoin", text):
            key = self._guess_join_key(text)
            return self._tool_propose_join(draft, left_key=key, right_key=key, preview=preview)

        if content.matches("setColumns", text):
            cols = self._parse_columns(text)
            if cols:
                return self._tool_set_columns(draft, cols, preview)

        params = self._parse_params_from_message(text)
        if params and (draft.get("sources") or []):
            # Enriquece com S2S when disponível (não bloqueia se AI cair).
            try:
                from tv_app.infrastructure.gateways.minha_delpi_ai_client import MinhaDelpiAiClient

                primary = find_source(draft, local_id=str(draft.get("primaryLocalId") or ""))
                op_id = str((primary or {}).get("operationId") or "") or None
                remote = MinhaDelpiAiClient().suggest_operational_params(query=text, operation_id=op_id)
                remote_params = remote.get("params") if isinstance(remote, dict) else None
                if isinstance(remote_params, dict):
                    for key, value in remote_params.items():
                        if value is not None and value != "" and key not in params:
                            params[key] = value
            except Exception as exc:  # noqa: BLE001
                logger.debug("suggest-params S2S skipped: %s", exc)
            return self._tool_set_params(draft, params, preview=preview)

        return self._tool_suggest(draft, text, preview)

    def _tool_suggest(
        self,
        draft: dict[str, Any],
        query: str,
        preview: Any,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], Any]:
        limit = TvDataBuilderContentService.setting_int("suggestLimit", 5)
        result = self._suggest.suggest(query=query, limit=limit)
        suggestions = result.get("suggestions") or []
        cards = [
            {
                "operationId": item.get("operationId"),
                "label": item.get("label"),
                "reason": item.get("reason") or "",
                "category": item.get("category"),
                "path": item.get("path"),
            }
            for item in suggestions
            if isinstance(item, dict)
        ]
        if result.get("degraded"):
            text = TvDataBuilderContentService.message("suggestDegraded")
        elif not cards:
            text = TvDataBuilderContentService.message("suggestEmpty")
        else:
            text = TvDataBuilderContentService.message(
                "suggestHeader",
                count=len(cards),
                query=query,
            )
        return draft, [_msg("assistant", text, suggestions=cards, tool="suggest_sources")], preview

    def _tool_add_source(
        self,
        draft: dict[str, Any],
        operation_id: str,
        preview: Any,
        *,
        params: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], Any]:
        route = self._catalog.get_route(operation_id)
        if not route:
            return (
                draft,
                [_msg("assistant", TvDataBuilderContentService.message("suggestEmpty"), tool="add_source")],
                preview,
            )
        max_sources = TvDataBuilderContentService.setting_int("maxSources", 8)
        if len(draft.get("sources") or []) >= max_sources:
            return (
                draft,
                [
                    _msg(
                        "assistant",
                        TvDataBuilderContentService.message(
                            "maxSourcesReached", count=max_sources
                        ),
                        tool="add_source",
                    )
                ],
                preview,
            )
        label = str(route.get("label") or operation_id)
        merged_params = apply_catalog_param_defaults(params or {}, route)
        draft, source = add_source(
            draft,
            operation_id=str(route.get("operationId") or operation_id),
            label=label,
            params=merged_params,
        )
        if source is None:
            text = TvDataBuilderContentService.message("sourceAlreadyAdded", label=label)
        else:
            text = TvDataBuilderContentService.message("sourceAdded", label=label)
        return draft, [_msg("assistant", text, tool="add_source")], preview

    def _tool_remove_source(
        self,
        draft: dict[str, Any],
        *,
        local_id: str | None = None,
        operation_id: str | None = None,
        preview: Any,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], Any]:
        draft, removed = remove_source(draft, local_id=local_id, operation_id=operation_id)
        if not removed:
            text = TvDataBuilderContentService.message("sourceNotFound")
        else:
            text = TvDataBuilderContentService.message(
                "sourceRemoved",
                label=str(removed.get("label") or removed.get("operationId") or ""),
            )
        return draft, [_msg("assistant", text, tool="remove_source")], preview

    def _tool_set_params(
        self,
        draft: dict[str, Any],
        params: dict[str, Any],
        *,
        local_id: str | None = None,
        preview: Any,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], Any]:
        draft, updated = set_params(draft, params=params, local_id=local_id)
        if not updated:
            text = TvDataBuilderContentService.message("sourceNotFound")
        else:
            text = TvDataBuilderContentService.message(
                "paramsUpdated",
                label=str(updated.get("label") or updated.get("operationId") or ""),
            )
        return draft, [_msg("assistant", text, tool="set_params")], preview

    def _tool_set_columns(
        self,
        draft: dict[str, Any],
        columns: list[str],
        preview: Any,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], Any]:
        draft = set_columns(draft, columns)
        text = TvDataBuilderContentService.message("columnsUpdated", count=len(columns))
        return draft, [_msg("assistant", text, tool="set_columns")], preview

    def _tool_propose_join(
        self,
        draft: dict[str, Any],
        *,
        left_key: str,
        right_key: str | None,
        preview: Any,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], Any]:
        sources = draft.get("sources") or []
        if len(sources) < 2:
            text = TvDataBuilderContentService.message("joinNeedTwoSources")
            return draft, [_msg("assistant", text, tool="propose_join")], preview
        draft, step = propose_join(draft, left_key=left_key, right_key=right_key)
        if not step:
            text = TvDataBuilderContentService.message("joinNeedTwoSources")
            return draft, [_msg("assistant", text, tool="propose_join")], preview
        left = find_source(draft, local_id=str(draft.get("primaryLocalId") or ""))
        right = find_source(draft, local_id=str(step.get("sourceId") or ""))
        text = TvDataBuilderContentService.message(
            "joinProposed",
            left=str((left or {}).get("label") or "fonte A"),
            right=str((right or {}).get("label") or "fonte B"),
            joinKey=left_key,
        )
        return draft, [_msg("assistant", text, tool="propose_join")], preview

    def _tool_mark_ready(
        self,
        draft: dict[str, Any],
        preview: Any,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], Any]:
        sources = draft.get("sources") or []
        if not sources:
            text = TvDataBuilderContentService.message("markReadyEmpty")
            draft = {**draft, "status": "draft"}
        else:
            draft = {**draft, "status": "ready"}
            text = TvDataBuilderContentService.message("markReady", count=len(sources))
        return draft, [_msg("assistant", text, tool="mark_ready")], preview

    @staticmethod
    def _parse_columns(text: str) -> list[str]:
        # «só colunas OP, days_late e filial» ou «colunas: a, b»
        lowered = text.lower()
        for marker in ("colunas:", "colunas ", "só ", "apenas "):
            idx = lowered.find(marker)
            if idx >= 0:
                tail = text[idx + len(marker) :]
                parts = re.split(r"[,;]| e ", tail, flags=re.IGNORECASE)
                cols = []
                for part in parts:
                    token = re.sub(r"[^a-zA-Z0-9_]+", "", part.strip().replace(" ", "_"))
                    if token and token.lower() not in {"colunas", "coluna", "so", "apenas"}:
                        cols.append(token)
                return cols
        return []

    @staticmethod
    def _guess_join_key(text: str) -> str:
        lowered = text.lower()
        for key in ("days_late", "operation_id", "product_code", "op", "ordem"):
            if key in lowered:
                return "op" if key in {"op", "ordem"} else key
        return "op"

    @classmethod
    def _parse_params_from_message(cls, text: str) -> dict[str, Any]:
        params: dict[str, Any] = {}
        branch = TvDataBuilderContentService.first_group("branch", text)
        if branch:
            # normalize «filial 01» capture
            token = branch.upper().replace("FILIAL", "").replace("BRANCH", "").strip()
            token = re.sub(r"\s+", "", token)
            if token in {"1", "01"}:
                token = "01"
            elif token in {"2", "02"}:
                token = "02"
            if token:
                params["branch"] = token
        days = TvDataBuilderContentService.first_group("periodDays", text)
        if days and days.isdigit():
            params["periodDays"] = int(days)
        return params
