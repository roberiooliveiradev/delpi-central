"""Monta excerpt schema-first do último resultado operacional (working memory)."""

from __future__ import annotations

import json
from typing import Any

from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_turn_grounding_content_service import (
    ChatTurnGroundingContentService,
)


class ChatLastResultExcerptService:
    @classmethod
    def build(
        cls,
        tool_calls: list[Any] | None,
        *,
        message_id: str | None = None,
    ) -> dict[str, Any] | None:
        selected = cls._select_primary_tool_call(tool_calls)

        if not selected:
            return None

        metadata = selected.get("metadata")

        if not isinstance(metadata, dict) or not metadata.get("ok"):
            return None

        path = str(metadata.get("path") or "").strip()
        action_id = str(metadata.get("actionId") or "").strip()
        operation_id = str(metadata.get("operationId") or action_id or "").strip()
        api_meta = metadata.get("apiDelpiResponseMeta")

        if not isinstance(api_meta, dict):
            api_meta = {}

        entity = str(api_meta.get("entity") or "").strip()
        profile_key = cls._resolve_profile_key(metadata)
        presentation_type = cls._resolve_presentation_type(metadata)
        title = cls._resolve_title(metadata)
        row_count = cls._resolve_row_count(metadata)
        top_keys = cls._extract_top_keys(metadata)
        keys_by_component_type = cls._extract_keys_by_component_type(metadata)
        preview = cls._build_preview(metadata)

        excerpt: dict[str, Any] = {
            "operationId": operation_id or None,
            "actionId": action_id or None,
            "path": path or None,
            "profileKey": profile_key or None,
            "entity": entity or None,
            "presentationType": presentation_type or None,
            "title": title or None,
            "rowCount": row_count,
            "topKeys": top_keys,
            "preview": preview or None,
            "messageId": str(message_id).strip() if message_id else None,
        }

        if keys_by_component_type:
            excerpt["keysByComponentType"] = keys_by_component_type

        return {key: value for key, value in excerpt.items() if value is not None}

    @classmethod
    def _select_primary_tool_call(cls, tool_calls: list[Any] | None) -> dict[str, Any] | None:
        primary: dict[str, Any] | None = None
        fallback: dict[str, Any] | None = None

        for tool_call in reversed(tool_calls or []):
            if not isinstance(tool_call, dict):
                continue

            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            role = str(metadata.get("compositionRole") or "").strip().lower()

            if role == "enrichment":
                fallback = fallback or tool_call
                continue

            primary = tool_call
            break

        return primary or fallback

    @classmethod
    def _resolve_profile_key(cls, metadata: dict[str, Any]) -> str | None:
        data_answer = metadata.get("dataAnswer")

        if isinstance(data_answer, dict):
            profile = str(data_answer.get("profileKey") or "").strip()

            if profile:
                return profile

        presentation_profile = metadata.get("presentationProfile")

        if isinstance(presentation_profile, dict):
            profile = str(presentation_profile.get("profileKey") or "").strip()

            if profile:
                return profile

        return None

    @classmethod
    def _resolve_presentation_type(cls, metadata: dict[str, Any]) -> str | None:
        for key in (
            "presentation",
            "treePresentation",
            "tablePresentation",
            "textPresentation",
            "kpiPresentation",
            "chartPresentation",
        ):
            block = metadata.get(key)

            if isinstance(block, dict):
                ptype = str(block.get("type") or "").strip()

                if ptype:
                    return ptype

        return None

    @classmethod
    def _resolve_title(cls, metadata: dict[str, Any]) -> str | None:
        for key in (
            "presentation",
            "treePresentation",
            "tablePresentation",
            "textPresentation",
            "kpiPresentation",
            "chartPresentation",
        ):
            block = metadata.get(key)

            if isinstance(block, dict):
                title = str(block.get("title") or "").strip()

                if title:
                    return title

        humanized = metadata.get("humanizedSummary")

        if isinstance(humanized, dict):
            title = str(humanized.get("titulo") or "").strip()

            if title:
                return title

        return None

    @classmethod
    def _resolve_row_count(cls, metadata: dict[str, Any]) -> int | None:
        summary = metadata.get("summary")

        if isinstance(summary, dict):
            for key in ("totalCount", "rowCount", "itemCount", "count"):
                value = summary.get(key)

                if isinstance(value, int) and value >= 0:
                    return value

        pagination = metadata.get("pagination")

        if isinstance(pagination, dict):
            total = pagination.get("total")

            if isinstance(total, int) and total >= 0:
                return total

        payload = cls._load_response_preview(metadata)

        if isinstance(payload, dict):
            for key in ("items", "rows", "data"):
                items = payload.get(key)

                if isinstance(items, list):
                    return len(items)

            root = payload.get("root")

            if isinstance(root, dict):
                children = root.get("children") or root.get("items")

                if isinstance(children, list) and children:
                    return len(children)

        table_presentations = metadata.get("tablePresentations")

        if isinstance(table_presentations, list):
            total_rows = 0

            for table in table_presentations:
                if not isinstance(table, dict):
                    continue

                rows = table.get("rows")

                if isinstance(rows, list):
                    total_rows += len(rows)

            if total_rows > 0:
                return total_rows

        tree = metadata.get("treePresentation")

        if isinstance(tree, dict):
            root = tree.get("root")

            if isinstance(root, dict):
                children = root.get("children")

                if isinstance(children, list) and children:
                    return len(children)

        return None

    @classmethod
    def _build_preview(cls, metadata: dict[str, Any]) -> str:
        preview = str(metadata.get("responsePreview") or "").strip()
        humanized = metadata.get("humanizedSummary")

        if isinstance(humanized, dict):
            lines = [str(humanized.get("titulo") or "").strip()]
            lines.extend(
                str(line).strip()
                for line in (humanized.get("linhas") or [])
                if str(line).strip()
            )
            humanized_text = "\n".join(line for line in lines if line)

            if humanized_text:
                preview = (
                    f"{humanized_text}\n\n{preview}" if preview else humanized_text
                )

        max_chars = ChatTurnGroundingContentService.max_preview_chars()

        if max_chars > 0 and len(preview) > max_chars:
            return f"{preview[:max_chars]}\n…"

        return preview

    @classmethod
    def _extract_top_keys(cls, metadata: dict[str, Any]) -> list[str]:
        max_keys = ChatTurnGroundingContentService.max_top_keys()
        field_names = {
            str(item).strip().lower()
            for item in ChatTurnGroundingContentService.extract_key_fields()
            if str(item).strip()
        }

        if not field_names or max_keys < 1:
            return []

        keys: list[str] = []
        seen: set[str] = set()

        def add_candidate(value: Any) -> None:
            if len(keys) >= max_keys:
                return

            code = ChatProductQueryIntentService.normalize_product_code(
                str(value or "").strip()
            )

            if not code or code in seen:
                return

            seen.add(code)
            keys.append(code)

        payload = cls._load_response_preview(metadata)

        if isinstance(payload, dict):
            for collection_key in ("items", "rows", "data"):
                collection = payload.get(collection_key)

                if isinstance(collection, list):
                    for item in collection:
                        if isinstance(item, dict):
                            cls._collect_keys_from_object(item, field_names, add_candidate)

            for collection_key in ("children",):
                collection = payload.get(collection_key)

                if isinstance(collection, list):
                    for item in collection:
                        cls._collect_keys_from_object(item, field_names, add_candidate)

                root = payload.get("root")

                if isinstance(root, dict):
                    nested = root.get("children") or root.get("items")

                    if isinstance(nested, list):
                        for item in nested:
                            cls._collect_keys_from_object(item, field_names, add_candidate)

        if keys:
            return keys[:max_keys]

        if isinstance(payload, dict):
            cls._collect_keys_from_object(payload, field_names, add_candidate)

        for table in metadata.get("tablePresentations") or []:
            if not isinstance(table, dict):
                continue

            for row in table.get("rows") or []:
                if not isinstance(row, dict):
                    continue

                cls._collect_keys_from_object(row, field_names, add_candidate)

        tree = metadata.get("treePresentation")

        if isinstance(tree, dict):
            root = tree.get("root")

            if isinstance(root, dict):
                nested = root.get("children") or root.get("items")

                if isinstance(nested, list):
                    for item in nested:
                        cls._collect_keys_from_object(item, field_names, add_candidate)

            if not keys:
                cls._collect_keys_from_object(tree, field_names, add_candidate)

        path = str(metadata.get("path") or "")
        path_code = ChatAnalysisIntentService.extract_product_code_from_tool_path(path)

        if path_code and not keys:
            add_candidate(path_code)

        return keys[:max_keys]

    @classmethod
    def _extract_keys_by_component_type(cls, metadata: dict[str, Any]) -> dict[str, list[str]]:
        buckets: dict[str, list[str]] = {"PI": [], "MP": []}
        seen: dict[str, set[str]] = {"PI": set(), "MP": set()}
        type_fields = ChatTurnGroundingContentService.component_type_fields()
        code_fields = {
            str(item).strip().lower()
            for item in ChatTurnGroundingContentService.extract_key_fields()
            if str(item).strip()
        }

        def add_code(component_type: str, value: Any) -> None:
            normalized_type = str(component_type or "").strip().upper()

            if normalized_type not in buckets:
                return

            code = ChatProductQueryIntentService.normalize_product_code(
                str(value or "").strip()
            )

            if not code or code in seen[normalized_type]:
                return

            cap = ChatTurnGroundingContentService.max_top_keys_for_component_type(
                normalized_type
            )

            if len(buckets[normalized_type]) >= cap:
                return

            seen[normalized_type].add(code)
            buckets[normalized_type].append(code)

        def resolve_type(node: dict[str, Any]) -> str:
            for field in type_fields:
                raw = node.get(field)

                if raw not in (None, ""):
                    return str(raw).strip().upper()

            return ""

        def resolve_code(node: dict[str, Any]) -> str:
            for field in code_fields:
                raw = node.get(field)

                if raw not in (None, ""):
                    return str(raw).strip()

            label = node.get("label")

            if label not in (None, ""):
                return str(label).strip()

            return ""

        def walk_node(node: Any) -> None:
            if isinstance(node, dict):
                component_type = resolve_type(node)
                code = resolve_code(node)

                if component_type in buckets and code:
                    add_code(component_type, code)

                for child_key in ("children", "components", "items"):
                    children = node.get(child_key)

                    if isinstance(children, list):
                        for child in children:
                            walk_node(child)

                return

            if isinstance(node, list):
                for item in node:
                    walk_node(item)

        payload = cls._load_response_preview(metadata)

        if isinstance(payload, dict):
            walk_node(payload)

        tree = metadata.get("treePresentation")

        if isinstance(tree, dict):
            walk_node(tree.get("root") or tree)

        result = {
            key: values
            for key, values in buckets.items()
            if values
        }

        return result

    @classmethod
    def _collect_keys_from_object(
        cls,
        node: Any,
        field_names: set[str],
        add_candidate,
    ) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if str(key).strip().lower() in field_names:
                    add_candidate(value)

                if isinstance(value, (dict, list)):
                    cls._collect_keys_from_object(value, field_names, add_candidate)

            return

        if isinstance(node, list):
            for item in node:
                cls._collect_keys_from_object(item, field_names, add_candidate)

    @classmethod
    def _load_response_preview(cls, metadata: dict[str, Any]) -> dict[str, Any] | list[Any] | None:
        raw = str(metadata.get("responsePreview") or "").strip()

        if not raw or not raw.startswith(("{", "[")):
            return None

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return None

        return parsed if isinstance(parsed, (dict, list)) else None
