"""Pipeline transversal de resolução de rótulos de campo (bundle canônico)."""

from __future__ import annotations

from typing import Any, Iterable

from app.domain.entities.field_label_bundle import FieldLabelBundle
from app.domain.services.chat_presentation_field_label_resolution_service import (
    ChatPresentationFieldLabelResolutionService,
)
from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)


class ChatFieldLabelResolutionPipelineService:
    """Orquestra um resolve único → FieldLabelBundle (delega à cascata R17)."""

    _column_labels = ExternalActionColumnLabelService()

    @classmethod
    def resolve(
        cls,
        keys: Iterable[str],
        *,
        path: str = "",
        profile_name: str | None = None,
        schema_labels: dict[str, str] | None = None,
        schema_formats: dict[str, str] | None = None,
        openapi_labels: dict[str, str] | None = None,
        enable_discovery: bool = True,
    ) -> FieldLabelBundle:
        ordered = [str(key).strip() for key in keys if str(key or "").strip()]
        return cls._column_labels.resolve_field_label_bundle(
            ordered,
            path=path,
            profile_name=profile_name,
            schema_labels=schema_labels,
            schema_formats=schema_formats,
            openapi_labels=openapi_labels,
            enable_discovery=enable_discovery,
        )

    @classmethod
    def resolve_label(
        cls,
        key: str,
        *,
        path: str = "",
        profile_name: str | None = None,
        schema_labels: dict[str, str] | None = None,
        enable_discovery: bool = True,
    ) -> str:
        return ChatPresentationFieldLabelResolutionService.resolve_label(
            key,
            path=path,
            profile_name=profile_name,
            schema_labels=schema_labels,
            enable_discovery=enable_discovery,
        )

    @classmethod
    def bundle_from_metadata(cls, metadata: dict[str, Any] | None) -> FieldLabelBundle:
        return FieldLabelBundle.from_metadata(metadata)

    @classmethod
    def label_from_metadata(
        cls,
        metadata: dict[str, Any] | None,
        key: str,
        *,
        default: str | None = None,
        path: str = "",
        enable_discovery: bool = False,
    ) -> str:
        token = str(key or "").strip()
        if not token:
            return str(default or "")

        bundle = cls.bundle_from_metadata(metadata)
        resolved = bundle.label_for(token)
        if resolved:
            return resolved

        if isinstance(metadata, dict):
            for presentation_key in (
                "presentation",
                "tablePresentation",
                "chartPresentation",
                "kpiPresentation",
            ):
                presentation = metadata.get(presentation_key)
                from_config = cls._label_from_presentation(presentation, token)
                if from_config:
                    return from_config

            tables = metadata.get("tablePresentations")
            if isinstance(tables, list):
                for presentation in tables:
                    from_config = cls._label_from_presentation(presentation, token)
                    if from_config:
                        return from_config

        if default is not None:
            return str(default)

        return cls.resolve_label(
            token,
            path=path or str((metadata or {}).get("path") or ""),
            enable_discovery=enable_discovery,
        )

    @classmethod
    def _label_from_presentation(cls, presentation: Any, key: str) -> str:
        if not isinstance(presentation, dict):
            return ""

        columns = presentation.get("columns")
        if isinstance(columns, list):
            for column in columns:
                if not isinstance(column, dict):
                    continue
                if str(column.get("key") or "").strip() != key:
                    continue
                label = str(column.get("label") or "").strip()
                if label:
                    return label

        config = presentation.get("config")
        if isinstance(config, dict):
            field_labels = config.get("fieldLabels")
            if isinstance(field_labels, dict):
                label = str(field_labels.get(key) or "").strip()
                if label:
                    return label

        return ""
