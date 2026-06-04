"""Resolve referências vagas (follow-up) para entidades da memória de turno."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_follow_up_intent_service import ChatFollowUpIntentService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatReferenceResolutionService:
    _PRODUCT_REF_RE = re.compile(
        r"\b(?:esse|esta|esse\s+mesmo)\s+(?:produto|item|c[oó]digo)\b",
        re.IGNORECASE,
    )
    _PERIOD_REF_RE = re.compile(
        r"\bmesmo\s+per[ií]odo\b|\bmesmo\s+intervalo\b",
        re.IGNORECASE,
    )
    _TABLE_REF_RE = re.compile(
        r"\b(?:essa|esta)\s+tabela\b|\btabela\s+anterior\b",
        re.IGNORECASE,
    )
    _CHART_REF_RE = re.compile(
        r"\b(?:esse|esta)\s+gr[aá]fico\b|\bgr[aá]fico\s+anterior\b",
        re.IGNORECASE,
    )
    _SAME_ACTION_RE = re.compile(
        r"\bfa[cç]a\s+o\s+mesmo\b|\brepete?\b.*\bconsulta\b",
        re.IGNORECASE,
    )
    _THIS_RE = re.compile(r"\b(?:isso|essa\s+resposta)\b", re.IGNORECASE)
    _THAT_RE = re.compile(r"\b(?:esse|essa|aquele|aquela)\b", re.IGNORECASE)
    _PREVIOUS_RE = re.compile(
        r"\b(?:o\s+)?anterior\b|\bresposta\s+anterior\b|\búltima\s+resposta\b",
        re.IGNORECASE,
    )
    _CANVAS_RE = re.compile(r"\b(?:a\s+)?lousa\b|\bno\s+canvas\b", re.IGNORECASE)
    _ATTACHMENT_RE = re.compile(
        r"\b(?:esse|este|o)\s+arquivo\b|\b(?:o\s+)?anexo\b|\bdo\s+anexo\b",
        re.IGNORECASE,
    )
    _SQL_EDIT_RE = re.compile(
        r"\b(?:adicione|inclua|acrescente)\s+(?:uma\s+)?coluna\b|"
        r"\b(?:essa|esta)\s+consulta\b|\bquery\s+anterior\b|\b(?:na|à)\s+consulta\b",
        re.IGNORECASE,
    )
    _CODE_REF_RE = re.compile(r"\b(?:esse|este)\s+c[oó]digo\b", re.IGNORECASE)
    _LAST_QUERY_RE = re.compile(r"\búltima\s+consulta\b", re.IGNORECASE)
    _COMPARE_PREVIOUS_RE = re.compile(
        r"\bcompare?\s+com\s+o\s+anterior\b",
        re.IGNORECASE,
    )

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
            operational_follow_up or cls._PRODUCT_REF_RE.search(normalized)
        ):
            resolved.append(
                cls._entry(
                    text="esse produto" if cls._PRODUCT_REF_RE.search(normalized) else "follow-up operacional",
                    resolved_to="productCode",
                    value=product_code,
                    source="operationalFocus.productCode",
                    confidence=0.9,
                )
            )
            used_keys.append("productCode")

        if branch and "filial" not in normalized.lower():
            if operational_follow_up or re.search(r"\bmesma\s+filial\b", normalized, re.I):
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

        if period and cls._PERIOD_REF_RE.search(normalized):
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

        if cls._TABLE_REF_RE.search(normalized) and last_presentation.get("type") == "table":
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

        if cls._CHART_REF_RE.search(normalized) and last_presentation.get("type") in {
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

        if cls._SAME_ACTION_RE.search(normalized) and isinstance(last_action, dict):
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

        if cls._CANVAS_RE.search(normalized) and isinstance(canvas, dict) and canvas.get("active"):
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

        if cls._ATTACHMENT_RE.search(normalized) and isinstance(last_attachment, dict):
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

        if cls._SQL_EDIT_RE.search(normalized) and last_sql:
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

        if cls._CODE_REF_RE.search(normalized) and product_code:
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

        if cls._PREVIOUS_RE.search(normalized) or cls._LAST_QUERY_RE.search(normalized):
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

        if cls._THIS_RE.search(normalized):
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
            cls._THAT_RE.search(normalized)
            and not cls._PRODUCT_REF_RE.search(normalized)
            and not resolved
            and not operational_follow_up
        ):
            cls._set_this_ambiguity(snapshot)

        return resolved, used_keys

    @classmethod
    def _set_this_ambiguity(cls, snapshot: dict) -> None:
        snapshot["memoryAmbiguity"] = {
            "reason": "this_reference",
            "promptHint": (
                "Quando você diz «isso» ou «esse», você quer a última resposta, "
                "a tabela/gráfico, a lousa ou o arquivo anexado?"
            ),
        }

    @classmethod
    def detect_ambiguity(cls, message: str, snapshot: dict | None) -> dict[str, Any] | None:
        if not cls._COMPARE_PREVIOUS_RE.search(message or ""):
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
            "promptHint": "Pergunte qual produto o usuário quer comparar antes de consultar.",
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
