"""Resolve referências vagas (follow-up) para entidades da memória de turno."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_follow_up_intent_service import ChatFollowUpIntentService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_reference_resolution_content_service import (
    ChatReferenceResolutionContentService,
)


class ChatReferenceResolutionService:
    @classmethod
    def _pattern(cls, key: str):
        return ChatReferenceResolutionContentService.compile_pattern(key)

    @classmethod
    def matches_compare_previous(cls, message: str) -> bool:
        return bool(cls._pattern("comparePrevious").search(message or ""))

    @classmethod
    def resolve(
        cls,
        message: str,
        operational_focus: dict[str, str] | None,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        return cls.resolve_from_snapshot(
            message,
            {"operationalFocus": operational_focus or {}},
        )

    @classmethod
    def resolve_from_snapshot(
        cls,
        message: str,
        snapshot: dict | None,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        from app.domain.services.chat_snapshot_operational_focus import (
            ChatSnapshotOperationalFocus,
        )

        if not isinstance(snapshot, dict):
            snapshot = {}

        entities = ChatSnapshotOperationalFocus.get(snapshot)
        last_action = snapshot.get("lastAction") or {}
        last_presentation = snapshot.get("lastPresentation") or {}
        used_keys: list[str] = []
        resolved: list[dict[str, Any]] = []
        normalized = (message or "").strip()

        if not normalized:
            return resolved, used_keys

        from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService

        if ChatSqlSafetyService.looks_like_sql_payload(message):
            return resolved, used_keys

        product_code = str(entities.get("productCode") or "").strip()
        branch = str(entities.get("branch") or "").strip()
        period = str(entities.get("period") or "").strip()
        explicit_code = ChatProductQueryIntentService.extract_product_code(message)

        operational_follow_up = ChatFollowUpIntentService.is_operational_follow_up(message)

        if product_code and not explicit_code and (
            operational_follow_up
            or cls._pattern("productRef").search(normalized)
            or cls._pattern("pronounCoref").search(normalized)
            or cls._pattern("previousRef").search(normalized)
        ):
            resolved.append(
                cls._entry(
                    text="esse produto" if cls._pattern("productRef").search(normalized) else "referência conversacional",
                    resolved_to="productCode",
                    value=product_code,
                    source="operationalFocus.productCode",
                    confidence=0.9,
                )
            )
            used_keys.append("productCode")

        if branch and "filial" not in normalized.lower():
            if operational_follow_up or cls._pattern("sameBranch").search(normalized):
                resolved.append(
                    cls._entry(
                        text="filial em contexto",
                        resolved_to="branch",
                        value=branch,
                        source="operationalFocus.branch",
                        confidence=0.75,
                    )
                )
                used_keys.append("branch")

        if period and cls._pattern("periodRef").search(normalized):
            resolved.append(
                cls._entry(
                    text="mesmo período",
                    resolved_to="period",
                    value=period,
                    source="operationalFocus.period",
                    confidence=0.85,
                )
            )
            used_keys.append("period")

        if cls._pattern("tableRef").search(normalized) and last_presentation.get("type") == "table":
            resolved.append(
                cls._entry(
                    text="essa tabela",
                    resolved_to="lastPresentation",
                    value=str(last_presentation.get("messageId") or "table"),
                    source="lastPresentation.type=table",
                    confidence=0.8,
                )
            )
            used_keys.append("lastPresentation")

        if cls._pattern("chartRef").search(normalized) and last_presentation.get("type") in {
            "chart",
            "line",
            "bar",
            "pie",
        }:
            resolved.append(
                cls._entry(
                    text="esse gráfico",
                    resolved_to="lastPresentation",
                    value=str(last_presentation.get("messageId") or "chart"),
                    source="lastPresentation.type=chart",
                    confidence=0.8,
                )
            )
            used_keys.append("lastPresentation")

        if cls._pattern("sameAction").search(normalized) and isinstance(last_action, dict):
            action_name = str(last_action.get("name") or "").strip()

            if action_name:
                resolved.append(
                    cls._entry(
                        text="faça o mesmo",
                        resolved_to="lastAction",
                        value=action_name,
                        source="lastAction.name",
                        confidence=0.85,
                    )
                )
                used_keys.append("lastAction")

        canvas = snapshot.get("canvas") or {}
        active_entities = snapshot.get("operationalFocus") or entities
        last_sql = str(active_entities.get("lastSqlSnippet") or "").strip()
        last_useful_id = str(snapshot.get("lastUsefulMessageId") or "").strip()

        if cls._pattern("canvasRef").search(normalized) and isinstance(canvas, dict) and canvas.get("active"):
            resolved.append(
                cls._entry(
                    text="lousa",
                    resolved_to="canvas",
                    value=str(canvas.get("lastUpdatedFromMessageId") or "canvas"),
                    source="canvas.active",
                    confidence=0.9,
                )
            )
            used_keys.append("canvas")

        last_attachment = snapshot.get("lastAttachment")

        if cls._pattern("attachmentRef").search(normalized) and isinstance(last_attachment, dict):
            filename = str(last_attachment.get("filename") or "").strip()

            if filename:
                resolved.append(
                    cls._entry(
                        text="arquivo/anexo",
                        resolved_to="lastAttachment",
                        value=filename,
                        source="lastAttachment.filename",
                        confidence=0.88,
                    )
                )
                used_keys.append("lastAttachment")

        if cls._pattern("sqlEdit").search(normalized) and last_sql:
            resolved.append(
                cls._entry(
                    text="consulta SQL",
                    resolved_to="lastSqlSnippet",
                    value=last_sql[:200],
                    source="operationalFocus.lastSqlSnippet",
                    confidence=0.9,
                )
            )
            used_keys.append("lastSqlSnippet")

        if cls._pattern("codeRef").search(normalized) and product_code:
            resolved.append(
                cls._entry(
                    text="esse código",
                    resolved_to="productCode",
                    value=product_code,
                    source="operationalFocus.productCode",
                    confidence=0.92,
                )
            )

            if "productCode" not in used_keys:
                used_keys.append("productCode")

        if cls._pattern("previousRef").search(normalized) or cls._pattern("lastQuery").search(normalized):
            if last_useful_id:
                resolved.append(
                    cls._entry(
                        text="resposta anterior",
                        resolved_to="lastUsefulMessage",
                        value=last_useful_id,
                        source="lastUsefulMessageId",
                        confidence=0.8,
                    )
                )
                used_keys.append("lastUsefulMessage")

            elif isinstance(last_action, dict) and last_action.get("name"):
                resolved.append(
                    cls._entry(
                        text="última consulta",
                        resolved_to="lastAction",
                        value=str(last_action.get("name")),
                        source="lastAction.name",
                        confidence=0.82,
                    )
                )
                used_keys.append("lastAction")

        if cls._pattern("thisRef").search(normalized):
            candidates: list[dict[str, Any]] = []

            if last_presentation.get("messageId"):
                candidates.append(
                    cls._entry(
                        text="isso",
                        resolved_to="lastPresentation",
                        value=str(last_presentation.get("messageId")),
                        source="lastPresentation.messageId",
                        confidence=0.75,
                    )
                )

            if isinstance(canvas, dict) and canvas.get("active"):
                candidates.append(
                    cls._entry(
                        text="isso",
                        resolved_to="canvas",
                        value=str(canvas.get("lastUpdatedFromMessageId") or "canvas"),
                        source="canvas.active",
                        confidence=0.7,
                    )
                )

            last_attachment = snapshot.get("lastAttachment")

            if isinstance(last_attachment, dict) and last_attachment.get("filename"):
                candidates.append(
                    cls._entry(
                        text="isso",
                        resolved_to="lastAttachment",
                        value=str(last_attachment.get("filename")),
                        source="lastAttachment.filename",
                        confidence=0.65,
                    )
                )

            if len(candidates) == 1:
                resolved.append(candidates[0])
                used_keys.append(candidates[0]["resolvedTo"])
            elif len(candidates) > 1:
                cls._set_this_ambiguity(snapshot)

        elif (
            cls._pattern("thatRef").search(normalized)
            and not cls._pattern("productRef").search(normalized)
            and not resolved
            and not operational_follow_up
        ):
            cls._set_this_ambiguity(snapshot)

        cls._append_result_set_references(
            normalized,
            snapshot,
            resolved=resolved,
            used_keys=used_keys,
        )
        cls._append_coreference_references(
            normalized,
            snapshot,
            explicit_code=explicit_code,
            resolved=resolved,
            used_keys=used_keys,
        )

        return resolved, used_keys

    @classmethod
    def _append_coreference_references(
        cls,
        message: str,
        snapshot: dict,
        *,
        explicit_code: str | None,
        resolved: list[dict[str, Any]],
        used_keys: list[str],
    ) -> None:
        """Correferência pronominal («ele», «nesse», «item anterior») ancorada no turno."""
        if explicit_code:
            return

        from app.domain.services.chat_result_set_reference_service import (
            ChatResultSetReferenceService,
        )

        already = {str(item.get("resolvedTo") or "") for item in resolved}
        result_set = ChatResultSetReferenceService.primary_set(snapshot)
        items = [
            item
            for item in ((result_set or {}).get("items") or [])
            if isinstance(item, dict) and str(item.get("code") or "").strip()
        ]

        def add(entry: dict[str, Any], key: str) -> None:
            resolved.append(entry)

            if key not in used_keys:
                used_keys.append(key)

        pronoun = cls._pattern("pronounCoref").search(message)
        list_scope = cls._pattern("resultSetScopeCoref").search(message)

        if (pronoun or list_scope) and len(items) == 1 and "resultSetItem" not in already:
            item = items[0]
            add(
                cls._entry(
                    text=ChatReferenceResolutionContentService.coreference_text(
                        "singleItemText",
                        default="único item da lista anterior",
                    ),
                    resolved_to="resultSetItem",
                    value=str(item.get("code") or "").strip(),
                    source="resultSets.items[1]",
                    confidence=ChatReferenceResolutionContentService.coreference_confidence(
                        "singleItemConfidence",
                        default=0.8,
                    ),
                ),
                "resultSets",
            )
            return

        if (
            cls._pattern("previousItemCoref").search(message)
            and len(items) >= 2
            and "resultSetItem" not in already
        ):
            add(
                cls._entry(
                    text=ChatReferenceResolutionContentService.coreference_text(
                        "previousItemText",
                        default="item anterior da lista",
                    ),
                    resolved_to="resultSetItem",
                    value=str(items[-2].get("code") or "").strip(),
                    source="resultSets.items[-2]",
                    confidence=ChatReferenceResolutionContentService.coreference_confidence(
                        "previousItemConfidence",
                        default=0.7,
                    ),
                ),
                "resultSets",
            )

    @classmethod
    def _append_result_set_references(
        cls,
        message: str,
        snapshot: dict,
        *,
        resolved: list[dict[str, Any]],
        used_keys: list[str],
    ) -> None:
        """Ordinais («o segundo», «os três primeiros») ancorados em ``resultSets``."""
        from app.domain.services.chat_result_set_reference_service import (
            ChatResultSetReferenceService,
        )

        entries, keys = ChatResultSetReferenceService.resolve(message, snapshot)

        if not entries:
            return

        resolved.extend(entries)

        for key in keys:
            if key not in used_keys:
                used_keys.append(key)

    @classmethod
    def _set_this_ambiguity(cls, snapshot: dict) -> None:
        snapshot["memoryAmbiguity"] = {
            "reason": "this_reference",
            "promptHint": ChatReferenceResolutionContentService.ambiguity_text(
                "thisReferencePromptHint"
            ),
        }

    @classmethod
    def detect_ambiguity(cls, message: str, snapshot: dict | None) -> dict[str, Any] | None:
        if not cls._pattern("comparePrevious").search(message or ""):
            return None

        entities = (snapshot or {}).get("operationalFocus") or {}
        product_code = str(entities.get("productCode") or "").strip()

        if not product_code:
            return None

        previous_codes: list[str] = []

        for item in (snapshot or {}).get("previousProductCodes") or []:
            code = str(item).strip()

            if code and code != product_code and code not in previous_codes:
                previous_codes.append(code)

        if len(previous_codes) < 1:
            return None

        return {
            "reason": "compare_previous",
            "candidates": [product_code, *previous_codes[:2]],
            "promptHint": ChatReferenceResolutionContentService.ambiguity_text("comparePreviousPromptHint"),
        }

    @staticmethod
    def _entry(
        *,
        text: str,
        resolved_to: str,
        value: str,
        source: str,
        confidence: float,
    ) -> dict[str, Any]:
        return {
            "text": text,
            "resolvedTo": resolved_to,
            "value": value,
            "source": source,
            "confidence": confidence,
        }
