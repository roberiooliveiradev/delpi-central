"""Extrai entidades, ações, apresentação, lousa e anexos do histórico da sessão."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService


class ChatConversationMemoryExtractor:
    _PERIOD_PATTERNS: tuple[tuple[str, str], ...] = (
        (r"\búltimos?\s+30\s+dias\b", "last_30_days"),
        (r"\bultimos?\s+30\s+dias\b", "last_30_days"),
        (r"\búltimos?\s+7\s+dias\b", "last_7_days"),
        (r"\bultimos?\s+7\s+dias\b", "last_7_days"),
        (r"\búltimo\s+m[eê]s\b", "last_month"),
        (r"\bultimo\s+m[eê]s\b", "last_month"),
        (r"\beste\s+m[eê]s\b", "current_month"),
    )

    _ACTION_FROM_PATH: tuple[tuple[str, str], ...] = (
        ("/stock", "stock_lookup"),
        ("/analyser", "product_analyser"),
        ("/description", "product_description"),
        ("/routing", "routing_lookup"),
        ("/structure", "structure_lookup"),
        ("/sales", "sales_lookup"),
    )

    @classmethod
    def enrich_snapshot(
        cls,
        snapshot: dict,
        *,
        previous_messages: list[Any] | None,
        tool_calls: list | None = None,
        attachments: list | None = None,
        agent_id: str | None = None,
        project_id: str | None = None,
    ) -> dict:
        result = dict(snapshot)
        entities = dict(result.get("operationalFocus") or {})

        period = cls._extract_period_from_messages(previous_messages)

        if period and not entities.get("period"):
            entities["period"] = period

        result["operationalFocus"] = entities
        result["lastAction"] = cls._extract_last_action(previous_messages, tool_calls)
        result["lastPresentation"] = cls._extract_last_presentation(previous_messages)
        result["lastResultExcerpt"] = cls._extract_last_result_excerpt(
            previous_messages,
            tool_calls,
        )
        result["recentMetricSnapshots"] = cls._extract_recent_metric_snapshots(
            previous_messages,
            tool_calls,
        )
        result["resultSets"] = cls._extract_result_sets(
            result,
            previous_messages=previous_messages,
            tool_calls=tool_calls,
        )
        result = cls._attach_contrast_metrics(result, tool_calls=tool_calls)
        result["canvas"] = cls._extract_canvas_state(previous_messages)
        result["lastAttachment"] = cls._extract_last_attachment(
            previous_messages,
            attachments,
        )

        if agent_id:
            result["activeAgentId"] = str(agent_id)

        if project_id:
            result["activeProjectId"] = str(project_id)

        return result

    @classmethod
    def _extract_period_from_messages(
        cls,
        previous_messages: list[Any] | None,
    ) -> str | None:
        for item in reversed(previous_messages or []):
            if cls._message_role(item) != "user":
                continue

            content = cls._message_content(item).lower()

            for pattern, value in cls._PERIOD_PATTERNS:
                if re.search(pattern, content, flags=re.IGNORECASE):
                    return value

        return None

    @classmethod
    def _extract_last_action(
        cls,
        previous_messages: list[Any] | None,
        tool_calls: list | None = None,
    ) -> dict[str, Any] | None:
        calls = list(tool_calls or [])

        if not calls:
            for item in reversed(previous_messages or []):
                metadata = cls._message_metadata(item)

                if cls._message_role(item) != "assistant":
                    continue

                stored = metadata.get("toolCalls") or []

                if stored:
                    calls = stored
                    break

        for tool_call in reversed(calls):
            if not isinstance(tool_call, dict):
                continue

            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            if str(metadata.get("compositionRole") or "").strip().lower() == "enrichment":
                continue

            path = str(metadata.get("path") or "")
            action_name = cls._action_name_from_path(path)
            params = cls._merge_executed_action_params(tool_call, metadata)

            code = ChatAnalysisIntentService.extract_product_code_from_tool_path(path)

            if code and "productCode" not in params:
                params["productCode"] = code

            result_type = cls._result_type_from_metadata(metadata)
            operation_id = cls._operation_id_from_metadata(metadata)
            action_id = str(
                tool_call.get("actionId")
                or metadata.get("actionId")
                or metadata.get("action_id")
                or ""
            ).strip()

            payload: dict[str, Any] = {
                "name": action_name,
                "params": params,
                "resultType": result_type,
                "path": path,
            }
            if operation_id:
                payload["operationId"] = operation_id
            if action_id:
                payload["actionId"] = action_id

            api_route_domain = str(metadata.get("apiRouteDomain") or "").strip()
            if api_route_domain:
                payload["apiRouteDomain"] = api_route_domain

            parameter_strategy = str(metadata.get("parameterStrategy") or "").strip()
            if parameter_strategy:
                payload["parameterStrategy"] = parameter_strategy

            return payload

        # Turno atual falhou (ex.: param inválido): preserva lastAction útil do histórico.
        if tool_calls:
            prior = cls._extract_last_action(previous_messages, tool_calls=None)
            if prior:
                return prior

        # Fallback: último ok mesmo se só houver enrichment (turno só follow-up).
        for tool_call in reversed(calls):
            if not isinstance(tool_call, dict):
                continue

            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            path = str(metadata.get("path") or "")
            action_name = cls._action_name_from_path(path)
            params = cls._merge_executed_action_params(tool_call, metadata)
            code = ChatAnalysisIntentService.extract_product_code_from_tool_path(path)

            if code and "productCode" not in params:
                params["productCode"] = code

            payload: dict[str, Any] = {
                "name": action_name,
                "params": params,
                "resultType": cls._result_type_from_metadata(metadata),
                "path": path,
            }
            operation_id = cls._operation_id_from_metadata(metadata)
            action_id = str(
                tool_call.get("actionId")
                or metadata.get("actionId")
                or metadata.get("action_id")
                or ""
            ).strip()
            if operation_id:
                payload["operationId"] = operation_id
            if action_id:
                payload["actionId"] = action_id
            api_route_domain = str(metadata.get("apiRouteDomain") or "").strip()
            if api_route_domain:
                payload["apiRouteDomain"] = api_route_domain
            parameter_strategy = str(metadata.get("parameterStrategy") or "").strip()
            if parameter_strategy:
                payload["parameterStrategy"] = parameter_strategy
            return payload

        return None

    @classmethod
    def _operation_id_from_metadata(cls, metadata: dict[str, Any]) -> str:
        operation_id = str(
            metadata.get("operationId") or metadata.get("operation_id") or ""
        ).strip()
        if operation_id:
            return operation_id
        api_meta = metadata.get("apiDelpiResponseMeta")
        if isinstance(api_meta, dict):
            return str(
                api_meta.get("operationId") or api_meta.get("operation_id") or ""
            ).strip()
        return ""

    @classmethod
    def _merge_executed_action_params(
        cls,
        tool_call: dict[str, Any],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Une arguments.parameters com requestParameters efetivos do envelope."""
        params: dict[str, Any] = {}
        sources: list[Any] = []

        args = tool_call.get("arguments")
        if isinstance(args, dict):
            sources.append(args.get("parameters"))

        sources.append(metadata.get("requestParameters"))
        sources.append(metadata.get("parameters"))

        continuity_keys = {
            "branch",
            "branch_code",
            "filial",
            "period",
            "start_date",
            "end_date",
            "productCode",
            "code",
            "granularity",
            "group_by",
            "limit",
            "page",
            "page_size",
        }

        for source in sources:
            if not isinstance(source, dict):
                continue
            for key, value in source.items():
                if value in (None, ""):
                    continue
                key_str = str(key)
                if key_str not in continuity_keys and key_str not in params:
                    # Mantém params HTTP extras já presentes no envelope.
                    if key_str.startswith("_") or key_str in {
                        "userMessage",
                        "message",
                        "queryText",
                        "query_text",
                        "sessionResponseFormat",
                        "presentationDetailFilter",
                    }:
                        continue
                canonical = (
                    "branch"
                    if key_str in {"branch_code", "filial"}
                    else key_str
                )
                if canonical == "code" and "productCode" not in params:
                    params["productCode"] = str(value)
                    continue
                params[canonical] = str(value) if not isinstance(value, (int, float, bool)) else value

        return params

    @classmethod
    def _extract_last_presentation(
        cls,
        previous_messages: list[Any] | None,
    ) -> dict[str, Any] | None:
        for item in reversed(previous_messages or []):
            if cls._message_role(item) != "assistant":
                continue

            metadata = cls._message_metadata(item)
            tool_calls = metadata.get("toolCalls") or []

            for tool_call in reversed(tool_calls):
                if not isinstance(tool_call, dict):
                    continue

                tool_meta = tool_call.get("metadata")

                if not isinstance(tool_meta, dict) or not tool_meta.get("ok"):
                    continue

                presentation = tool_meta.get("presentation")

                if isinstance(presentation, dict):
                    ptype = str(presentation.get("type") or "").strip()

                    if ptype:
                        return {
                            "type": ptype,
                            "title": presentation.get("title"),
                            "messageId": cls._message_id(item),
                        }

                text_presentation = tool_meta.get("textPresentation")

                if isinstance(text_presentation, dict):
                    return {
                        "type": "text",
                        "title": text_presentation.get("title"),
                        "messageId": cls._message_id(item),
                    }

            if metadata.get("contextSnapshot"):
                return {"type": "chat", "messageId": cls._message_id(item)}

        return None

    @classmethod
    def _extract_last_result_excerpt(
        cls,
        previous_messages: list[Any] | None,
        tool_calls: list | None = None,
    ) -> dict[str, Any] | None:
        from app.domain.services.chat_last_result_excerpt_service import (
            ChatLastResultExcerptService,
        )

        calls = list(tool_calls or [])
        message_id: str | None = None

        if not calls:
            for item in reversed(previous_messages or []):
                if cls._message_role(item) != "assistant":
                    continue

                metadata = cls._message_metadata(item)
                stored = metadata.get("toolCalls") or []

                if stored:
                    calls = stored
                    message_id = cls._message_id(item)
                    break
        elif previous_messages:
            for item in reversed(previous_messages or []):
                if cls._message_role(item) != "assistant":
                    continue

                metadata = cls._message_metadata(item)
                stored = metadata.get("toolCalls") or []

                if stored:
                    message_id = cls._message_id(item)
                    break

        return ChatLastResultExcerptService.build_preserving_structure_types(
            calls,
            message_id=message_id,
            previous_messages=previous_messages,
        )

    @classmethod
    def _extract_result_sets(
        cls,
        snapshot: dict[str, Any],
        *,
        previous_messages: list[Any] | None,
        tool_calls: list | None,
    ) -> list[dict[str, Any]]:
        from app.domain.services.chat_result_set_reference_service import (
            ChatResultSetReferenceService,
        )

        calls = list(tool_calls or [])
        message_id: str | None = None

        if not calls:
            for item in reversed(previous_messages or []):
                if cls._message_role(item) != "assistant":
                    continue

                stored = cls._message_metadata(item).get("toolCalls") or []

                if stored:
                    calls = stored
                    message_id = cls._message_id(item)
                    break

        return ChatResultSetReferenceService.build_result_sets(
            tool_calls=calls,
            excerpt=snapshot.get("lastResultExcerpt"),
            message_id=message_id,
            previous_result_sets=snapshot.get("resultSets"),
        )

    @classmethod
    def _extract_canvas_state(
        cls,
        previous_messages: list[Any] | None,
    ) -> dict[str, Any] | None:
        version = 0

        for item in reversed(previous_messages or []):
            metadata = cls._message_metadata(item)
            canvas_open = metadata.get("canvasOpen")

            if not isinstance(canvas_open, dict):
                continue

            markdown = str(canvas_open.get("markdown") or "").strip()

            if not markdown:
                continue

            version += 1

            return {
                "active": True,
                "title": str(canvas_open.get("title") or "Lousa").strip(),
                "lastUpdatedFromMessageId": cls._message_id(item),
                "lastContentType": "markdown",
                "version": version,
            }

        return {"active": False} if previous_messages else None

    @classmethod
    def _extract_last_attachment(
        cls,
        previous_messages: list[Any] | None,
        attachments: list | None,
    ) -> dict[str, Any] | None:
        if attachments:
            last = attachments[-1] if isinstance(attachments, list) else attachments

            if isinstance(last, dict):
                return {
                    "filename": last.get("filename") or last.get("name"),
                    "type": last.get("mimeType") or last.get("type"),
                    "parsed": bool(last.get("parsed") or last.get("textExtracted")),
                }

        for item in reversed(previous_messages or []):
            metadata = cls._message_metadata(item)
            msg_attachments = metadata.get("attachments") or []

            if not msg_attachments:
                continue

            last = msg_attachments[-1]

            if isinstance(last, dict):
                return {
                    "filename": last.get("filename") or last.get("name"),
                    "type": last.get("mimeType") or last.get("type"),
                    "parsed": bool(last.get("parsed")),
                    "messageId": cls._message_id(item),
                }

        return None

    @classmethod
    def _action_name_from_path(cls, path: str) -> str:
        lowered = (path or "").lower()

        for fragment, name in cls._ACTION_FROM_PATH:
            if fragment in lowered:
                return name

        return "external_action"

    @classmethod
    def _result_type_from_metadata(cls, metadata: dict) -> str:
        presentation = metadata.get("presentation")

        if isinstance(presentation, dict):
            ptype = str(presentation.get("type") or "").strip()

            if ptype == "table":
                return "table"

            if ptype in {"chart", "line", "bar", "pie"}:
                return "chart"

        if metadata.get("textPresentation"):
            return "text_block"

        return "unknown"

    @classmethod
    def _attach_contrast_metrics(
        cls,
        snapshot: dict[str, Any],
        *,
        tool_calls: list | None,
    ) -> dict[str, Any]:
        """Mantém consolidado × filial para challenge mesmo se o histórico truncar prosa."""
        result = dict(snapshot)
        prior_consolidated = (
            dict(result["lastConsolidatedMetric"])
            if isinstance(result.get("lastConsolidatedMetric"), dict)
            else None
        )
        prior_branch = (
            dict(result["lastBranchMetric"])
            if isinstance(result.get("lastBranchMetric"), dict)
            else None
        )
        last_action = result.get("lastAction")
        if not isinstance(last_action, dict):
            return result

        snaps = result.get("recentMetricSnapshots")
        if not isinstance(snaps, list) or not snaps:
            snaps = cls._extract_recent_metric_snapshots(None, tool_calls)

        branch = ""
        params = last_action.get("params")
        if isinstance(params, dict):
            branch = str(params.get("branch") or "").strip()

        def _pick(prefer_branch: bool) -> dict[str, Any] | None:
            for item in reversed(snaps or []):
                if not isinstance(item, dict):
                    continue
                item_branch = str(item.get("branch") or "").strip()
                is_branch = bool(item_branch) and item_branch.lower() not in {
                    "all",
                    "todas",
                }
                if prefer_branch and is_branch:
                    if branch and item_branch != branch:
                        continue
                    return dict(item)
                if not prefer_branch and not is_branch:
                    return dict(item)
            return None

        consolidated = _pick(False)
        branched = _pick(True) if branch and branch.lower() not in {"all", "todas"} else None

        if consolidated:
            result["lastConsolidatedMetric"] = consolidated
        elif prior_consolidated and branch and branch.lower() not in {"all", "todas"}:
            result["lastConsolidatedMetric"] = prior_consolidated
        elif not branch and snaps:
            for item in reversed(snaps):
                if isinstance(item, dict) and not str(item.get("branch") or "").strip():
                    result["lastConsolidatedMetric"] = dict(item)
                    break

        if branched:
            result["lastBranchMetric"] = branched
        elif branch and snaps:
            for item in reversed(snaps):
                if (
                    isinstance(item, dict)
                    and str(item.get("branch") or "").strip() == branch
                ):
                    result["lastBranchMetric"] = dict(item)
                    break
        elif prior_branch and branch:
            result["lastBranchMetric"] = prior_branch

        return result

    @classmethod
    def _extract_recent_metric_snapshots(
        cls,
        previous_messages: list[Any] | None,
        tool_calls: list | None = None,
        *,
        limit: int = 12,
    ) -> list[dict[str, Any]]:
        """KPI cards / valores em prosa recentes (consolidado × filial) para challenge grounded."""
        snapshots: list[dict[str, Any]] = []
        from app.domain.services.chat_follow_up_turn_content_service import (
            ChatFollowUpTurnContentService,
        )

        currency_re = ChatFollowUpTurnContentService.compile_pattern("currencyMetric")

        def _parse_brl(raw: str) -> float | None:
            token = str(raw or "").strip()
            if not token:
                return None
            try:
                return float(token.replace(".", "").replace(",", "."))
            except ValueError:
                return None

        def _consume_tools(calls: list | None) -> None:
            for tool_call in calls or []:
                if not isinstance(tool_call, dict):
                    continue
                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue
                meta = tool_call.get("metadata")
                if not isinstance(meta, dict) or not meta.get("ok"):
                    continue
                params = cls._merge_executed_action_params(tool_call, meta)
                branch = str(params.get("branch") or "").strip()
                kpi = meta.get("kpiPresentation")
                cards = kpi.get("cards") if isinstance(kpi, dict) else None
                if not isinstance(cards, list):
                    continue
                for card in cards:
                    if not isinstance(card, dict):
                        continue
                    raw = card.get("value")
                    try:
                        value = float(raw)
                    except (TypeError, ValueError):
                        continue
                    label = str(card.get("label") or card.get("key") or "Indicador").strip()
                    snapshots.append(
                        {
                            "label": label,
                            "value": value,
                            "display": cls._format_brl_display(value),
                            "branch": branch,
                        }
                    )

        for item in previous_messages or []:
            if cls._message_role(item) != "assistant":
                continue
            meta = cls._message_metadata(item)
            stored = meta.get("toolCalls") if isinstance(meta.get("toolCalls"), list) else None
            if not stored and isinstance(item, dict):
                top = item.get("toolCalls")
                stored = top if isinstance(top, list) else []
            if not stored:
                stored = []
            message_branch = ""
            if stored:
                before = len(snapshots)
                _consume_tools(stored)
                for snap in snapshots[before:]:
                    if snap.get("branch"):
                        message_branch = str(snap.get("branch") or "")
                        break
                if not message_branch:
                    for call in stored:
                        if not isinstance(call, dict):
                            continue
                        call_meta = (
                            call.get("metadata")
                            if isinstance(call.get("metadata"), dict)
                            else {}
                        )
                        params = cls._merge_executed_action_params(call, call_meta)
                        if params.get("branch"):
                            message_branch = str(params.get("branch") or "")
                            break

            content = cls._message_content(item)
            if content:
                for match in currency_re.finditer(content):
                    value = _parse_brl(match.group("value"))
                    if value is None:
                        continue
                    snapshots.append(
                        {
                            "label": match.group("label").strip(),
                            "value": value,
                            "display": f"R$ {match.group('value')}",
                            "branch": message_branch,
                        }
                    )

        if tool_calls:
            _consume_tools(tool_calls)

        if limit > 0 and len(snapshots) > limit:
            return snapshots[-limit:]
        return snapshots

    @staticmethod
    def _format_brl_display(value: float) -> str:
        formatted = f"{value:,.2f}"
        return "R$ " + formatted.replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    def _message_content(message: Any) -> str:
        if isinstance(message, dict):
            return str(message.get("content") or "")

        return str(getattr(message, "content", "") or "")

    @staticmethod
    def _message_role(message: Any) -> str:
        if isinstance(message, dict):
            return str(message.get("role") or "").strip().lower()

        return str(getattr(message, "role", "") or "").strip().lower()

    @staticmethod
    def _message_metadata(message: Any) -> dict:
        if isinstance(message, dict):
            meta = message.get("metadata")

            return meta if isinstance(meta, dict) else {}

        meta = getattr(message, "metadata", None)

        return meta if isinstance(meta, dict) else {}

    @staticmethod
    def _message_id(message: Any) -> str | None:
        if isinstance(message, dict):
            mid = message.get("id")

            return str(mid) if mid is not None else None

        mid = getattr(message, "id", None)

        return str(mid) if mid is not None else None
