"""Contrato SelectionPending — candidatos de catálogo com evidência opcional (Playbook 07)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


class ChatCatalogSelectionPendingService:
    """Monta metadata.selectionPending genérico a partir de candidatos ranqueados.

    Agnóstico de rota/KPI/TV: consumidores (score-gap, copiloto TV) só passam candidatos.
    """

    KIND_CATALOG_ROUTE = "catalog_route"
    KIND_SCORE_GAP_ROUTE = "score_gap_route"
    METADATA_KEY = "selectionPending"
    FOLLOW_UP_KEY = "selectionFollowUpSuggestions"

    @classmethod
    def _bundle(cls) -> dict[str, Any]:
        return ChatAssistantContentService.load_bundle("selection_pending")

    @classmethod
    def setting_int(cls, key: str, default: int) -> int:
        settings = cls._bundle().get("settings") or {}
        try:
            return int(settings.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def setting_float(cls, key: str, default: float) -> float:
        settings = cls._bundle().get("settings") or {}
        try:
            return float(settings.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def message(cls, key: str, **kwargs: Any) -> str:
        messages = cls._bundle().get("messages") or {}
        template = str(messages.get(key) or "").strip()
        if not template:
            return ""
        try:
            return template.format(**kwargs)
        except (KeyError, ValueError):
            return template

    @classmethod
    def build(
        cls,
        *,
        candidates: list[dict[str, Any]],
        kind: str = KIND_CATALOG_ROUTE,
        multi_select: bool | None = None,
        score_gap: float | None = None,
        prompt: str | None = None,
    ) -> dict[str, Any] | None:
        cleaned = cls._normalize_candidates(candidates, kind=kind)
        if not cleaned:
            return None

        kinds = cls._bundle().get("kinds") or {}
        kind_cfg = kinds.get(kind) if isinstance(kinds.get(kind), dict) else {}
        if multi_select is None:
            multi_select = bool(kind_cfg.get("multiSelectDefault", True))

        prompt_text = str(prompt or "").strip()
        if not prompt_text:
            prompt_key = str(kind_cfg.get("promptKey") or "promptCatalogRoute")
            prompt_text = cls.message(prompt_key, count=len(cleaned))

        confirm_key = str(kind_cfg.get("confirmLabelKey") or "confirmSelected")
        cancel_key = str(kind_cfg.get("cancelLabelKey") or "cancelSelection")

        return {
            "kind": kind,
            "multiSelect": bool(multi_select),
            "prompt": prompt_text,
            "scoreGap": score_gap,
            "candidates": cleaned,
            "confirmLabel": cls.message(confirm_key),
            "cancelLabel": cls.message(cancel_key),
            "resume": {
                "mode": "structured_action",
                "action": "catalog_route_selection",
            },
        }

    @classmethod
    def build_from_score_gap_clarification(
        cls,
        clarification: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(clarification, dict):
            return None
        suggestions = clarification.get("suggestions")
        if not isinstance(suggestions, list):
            return None
        candidates: list[dict[str, Any]] = []
        for item in suggestions:
            if not isinstance(item, dict):
                continue
            operation_id = str(item.get("operationId") or item.get("id") or "").strip()
            label = str(item.get("label") or operation_id).strip()
            if not operation_id and not label:
                continue
            candidates.append(
                {
                    "id": operation_id or label,
                    "label": label,
                    "score": item.get("score"),
                    "reason": str(item.get("reason") or "").strip() or None,
                    "operationId": operation_id or None,
                    "query": str(item.get("query") or label).strip(),
                }
            )
        gap = clarification.get("scoreGap")
        try:
            score_gap = float(gap) if gap is not None else None
        except (TypeError, ValueError):
            score_gap = None
        return cls.build(
            candidates=candidates,
            kind=cls.KIND_SCORE_GAP_ROUTE,
            multi_select=False,
            score_gap=score_gap,
        )

    @classmethod
    def build_from_route_candidates(
        cls,
        *,
        candidates: list[dict[str, Any]] | None,
        prompt: str | None = None,
        multi_select: bool = True,
    ) -> dict[str, Any] | None:
        rows: list[dict[str, Any]] = []
        for item in candidates or []:
            if not isinstance(item, dict):
                continue
            operation_id = str(
                item.get("operationId") or item.get("id") or ""
            ).strip()
            label = str(item.get("label") or operation_id).strip()
            if not operation_id:
                continue
            evidence = item.get("evidence")
            row: dict[str, Any] = {
                "id": operation_id,
                "label": label,
                "score": item.get("score"),
                "reason": str(item.get("reason") or "").strip() or None,
                "operationId": operation_id,
                "path": str(item.get("path") or "").strip() or None,
                "query": cls._resume_query_for_ids(
                    [operation_id],
                    kind=cls.KIND_CATALOG_ROUTE,
                ),
            }
            if isinstance(evidence, dict) and evidence:
                row["evidence"] = evidence
            rows.append(row)
        return cls.build(
            candidates=rows,
            kind=cls.KIND_CATALOG_ROUTE,
            multi_select=multi_select,
            prompt=prompt,
        )

    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict[str, Any],
        *,
        tool_context: dict[str, Any] | None = None,
        tool_calls: list | None = None,
    ) -> None:
        pending = None
        ctx = tool_context if isinstance(tool_context, dict) else {}

        raw = ctx.get(cls.METADATA_KEY)
        if isinstance(raw, dict) and raw.get("candidates"):
            pending = raw
        if pending is None:
            pending = cls.build_from_score_gap_clarification(
                ctx.get("routeSelectionClarification")
                if isinstance(ctx.get("routeSelectionClarification"), dict)
                else None
            )
        if pending is None:
            for call in tool_calls or []:
                if not isinstance(call, dict):
                    continue
                call_meta = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}
                if isinstance(call_meta.get(cls.METADATA_KEY), dict):
                    pending = call_meta.get(cls.METADATA_KEY)
                    break

        if not isinstance(pending, dict):
            return

        metadata[cls.METADATA_KEY] = pending
        follow_ups = cls.to_follow_up_suggestions(pending)
        if follow_ups:
            metadata[cls.FOLLOW_UP_KEY] = follow_ups

    @classmethod
    def to_follow_up_suggestions(
        cls,
        pending: dict[str, Any],
    ) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        for item in pending.get("candidates") or []:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or "").strip()
            query = str(item.get("query") or "").strip()
            if not label or not query:
                continue
            out.append({"label": label, "query": query})
        return out

    @classmethod
    def build_resume_message(
        cls,
        operation_ids: list[str],
        *,
        kind: str = KIND_CATALOG_ROUTE,
    ) -> str:
        ids = [str(item).strip() for item in operation_ids if str(item).strip()]
        if not ids:
            return ""
        return cls._resume_query_for_ids(ids, kind=kind)

    @classmethod
    def _resume_prefix_for_kind(cls, kind: str) -> str:
        kinds = cls._bundle().get("kinds") or {}
        kind_cfg = kinds.get(kind) if isinstance(kinds.get(kind), dict) else {}
        prefix_key = str(
            kind_cfg.get("resumePrefixKey")
            or ("resumePrefix" if kind == cls.KIND_CATALOG_ROUTE else "resumePrefixRoute")
        )
        return cls.message(prefix_key)

    @classmethod
    def _resume_query_for_ids(
        cls,
        operation_ids: list[str],
        *,
        kind: str = KIND_CATALOG_ROUTE,
    ) -> str:
        prefix = cls._resume_prefix_for_kind(kind)
        joined = ", ".join(operation_ids)
        if not prefix:
            return joined
        return f"{prefix} {joined}".strip()

    @classmethod
    def _normalize_candidates(
        cls,
        candidates: list[dict[str, Any]],
        *,
        kind: str = KIND_CATALOG_ROUTE,
    ) -> list[dict[str, Any]]:
        cap = cls.setting_int("maxCandidates", 5)
        out: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in candidates:
            if not isinstance(item, dict):
                continue
            candidate_id = str(item.get("id") or item.get("operationId") or "").strip()
            label = str(item.get("label") or candidate_id).strip()
            if not candidate_id or candidate_id in seen:
                continue
            seen.add(candidate_id)
            row: dict[str, Any] = {
                "id": candidate_id,
                "label": label,
                "score": item.get("score"),
                "reason": item.get("reason"),
                "operationId": item.get("operationId") or candidate_id,
                "path": item.get("path"),
                "query": str(item.get("query") or "").strip()
                or cls._resume_query_for_ids([candidate_id], kind=kind),
            }
            evidence = item.get("evidence")
            if isinstance(evidence, dict) and evidence.get("shape"):
                row["evidence"] = {
                    "shape": str(evidence.get("shape") or "table"),
                    "columns": evidence.get("columns")
                    if isinstance(evidence.get("columns"), list)
                    else [],
                    "rows": evidence.get("rows")
                    if isinstance(evidence.get("rows"), list)
                    else [],
                    "truncated": bool(evidence.get("truncated")),
                }
            out.append(row)
            if len(out) >= cap:
                break
        return out
