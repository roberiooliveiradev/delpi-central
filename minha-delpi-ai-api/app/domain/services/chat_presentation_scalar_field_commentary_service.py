"""Comentário humanizado para payloads campo-valor (meta.shape=scalar, KPIs departamentais)."""

from __future__ import annotations

from typing import Any, Callable

from app.domain.services.chat_humanized_data_response_content_service import (
    ChatHumanizedDataResponseContentService,
)
from app.domain.services.chat_humanized_data_response_service import (
    ChatHumanizedDataResponseService,
)
from app.domain.services.chat_operational_data_commentary_service import (
    ChatOperationalDataCommentaryService,
)

class ChatPresentationScalarFieldCommentaryService:
    """Detecta e resume dicts numéricos sem lista — desacoplado de rota/entidade específica."""

    @classmethod
    def matches(cls, metadata: dict[str, Any], data: dict[str, Any]) -> bool:
        if not isinstance(metadata, dict) or not isinstance(data, dict):
            return False

        if isinstance(data.get("items"), list):
            return False

        payload = cls._unwrap_payload(data)

        if not cls._has_numeric_metrics(payload):
            return False

        api_meta = cls._api_response_meta(metadata)
        shape = str(api_meta.get("shape") or "").strip().lower()
        configured_shapes = cls._configured_shapes()

        if shape and shape in configured_shapes:
            return True

        commentary_key = ChatOperationalDataCommentaryService.resolve_profile_key(
            path=str(metadata.get("path") or ""),
            metadata=metadata,
        )

        return str(commentary_key or "").strip() in cls._commentary_profile_keys()

    @classmethod
    def build(
        cls,
        metadata: dict[str, Any],
        data: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any] | None:
        if not cls.matches(metadata, data):
            return None

        from app.domain.services.external_actions.external_action_column_label_service import (
            ExternalActionColumnLabelService,
        )

        payload = cls._unwrap_payload(data)

        if not isinstance(payload, dict):
            return None

        api_meta = cls._api_response_meta(metadata)
        field_labels = api_meta.get("fields") if isinstance(api_meta.get("fields"), dict) else {}
        field_formats = (
            api_meta.get("fieldFormats") if isinstance(api_meta.get("fieldFormats"), dict) else {}
        )
        label_service = ExternalActionColumnLabelService()
        ordered_keys = cls._ordered_metric_keys(payload, field_labels=field_labels)

        if not ordered_keys:
            return None

        def fmt(field_key: str, value: object) -> str:
            if format_quantity:
                return format_quantity(value, field_key)

            return label_service.format_field_value(
                field_key,
                value,
                schema_formats=field_formats,
            )

        template = ChatHumanizedDataResponseContentService.get(
            "scalarFieldProfile",
            "highlightLineTemplate",
            default="**{label}:** {value}",
        )
        max_highlights = cls._max_highlights()
        highlights: list[str] = []

        for key in ordered_keys[:max_highlights]:
            label = str(field_labels.get(key) or key).strip()
            highlights.append(
                template.format(label=label, value=fmt(key, payload.get(key)))
            )

        lead = highlights[0] if highlights else ""
        profile_key = cls._commentary_profile_key(metadata)

        return ChatHumanizedDataResponseService.normalize(
            {
                "profileKey": profile_key,
                "highlights": highlights,
                "attention": [],
                "summaryLines": highlights[:4],
                "alertLevel": "ok" if lead else "unknown",
                "summary": lead,
                "visualHints": [cls._visual_hint()],
            },
            profile_key=profile_key,
        )

    @classmethod
    def _commentary_profile_key(cls, metadata: dict[str, Any]) -> str:
        resolved = ChatOperationalDataCommentaryService.resolve_profile_key(
            path=str(metadata.get("path") or ""),
            metadata=metadata,
        )
        token = str(resolved or "").strip()

        if token in cls._commentary_profile_keys():
            return token

        fallback = ChatHumanizedDataResponseContentService.get(
            "scalarFieldProfile",
            "defaultCommentaryProfileKey",
            default="generic_kpi_series",
        )

        return fallback or "generic_kpi_series"

    @classmethod
    def _ordered_metric_keys(
        cls,
        payload: dict[str, Any],
        *,
        field_labels: dict[str, Any],
    ) -> list[str]:
        skip = cls._skip_field_keys()
        ordered: list[str] = []

        for key in cls._primary_field_keys():
            if key in payload and key not in skip and cls._is_numeric(payload.get(key)):
                ordered.append(key)

        for key in field_labels:
            token = str(key).strip()

            if token and token not in skip and token not in ordered and cls._is_numeric(
                payload.get(token)
            ):
                ordered.append(token)

        for key in sorted(payload):
            token = str(key).strip()

            if token in skip or token in ordered:
                continue

            if cls._is_numeric(payload.get(token)):
                ordered.append(token)

        return ordered

    @classmethod
    def _has_numeric_metrics(cls, payload: dict[str, Any]) -> bool:
        if not isinstance(payload, dict):
            return False

        skip = cls._skip_field_keys()

        return any(
            str(key) not in skip and cls._is_numeric(value)
            for key, value in payload.items()
        )

    @classmethod
    def _is_numeric(cls, value: object) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    @classmethod
    def _unwrap_payload(cls, data: dict[str, Any]) -> dict[str, Any]:
        nested = data.get("data")

        if isinstance(nested, dict):
            return nested

        return data

    @classmethod
    def _api_response_meta(cls, metadata: dict[str, Any]) -> dict[str, Any]:
        api_meta = metadata.get("apiDelpiResponseMeta")

        return api_meta if isinstance(api_meta, dict) else {}

    @classmethod
    def _configured_shapes(cls) -> frozenset[str]:
        return frozenset(
            str(item).strip().lower()
            for item in ChatHumanizedDataResponseContentService.list(
                "scalarFieldProfile",
                "responseShapes",
            )
            if str(item).strip()
        )

    @classmethod
    def _commentary_profile_keys(cls) -> frozenset[str]:
        return frozenset(
            str(item).strip()
            for item in ChatHumanizedDataResponseContentService.list(
                "scalarFieldProfile",
                "commentaryProfileKeys",
            )
            if str(item).strip()
        )

    @classmethod
    def _skip_field_keys(cls) -> frozenset[str]:
        return frozenset(
            str(item).strip()
            for item in ChatHumanizedDataResponseContentService.list(
                "scalarFieldProfile",
                "skipFieldKeys",
            )
            if str(item).strip()
        )

    @classmethod
    def _primary_field_keys(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip()
            for item in ChatHumanizedDataResponseContentService.list(
                "scalarFieldProfile",
                "primaryFieldKeys",
            )
            if str(item).strip()
        )

    @classmethod
    def _max_highlights(cls) -> int:
        raw = ChatHumanizedDataResponseContentService.get_node(
            "scalarFieldProfile",
            "maxHighlights",
        )

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 8

    @classmethod
    def _visual_hint(cls) -> str:
        return ChatHumanizedDataResponseContentService.get(
            "scalarFieldProfile",
            "visualHint",
            default="field_value_profile",
        )
