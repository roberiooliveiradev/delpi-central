"""Resolução canônica de rótulo de display de action (não afeta routing)."""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger(__name__)

SOURCE_OPENAPI_SUMMARY = "OPENAPI_SUMMARY"
SOURCE_OPENAPI_LOCALIZED = "OPENAPI_LOCALIZED"
SOURCE_LEGACY_PATH_LABEL = "LEGACY_PATH_LABEL"
SOURCE_ENGLISH_SUMMARY_MAP = "ENGLISH_SUMMARY_MAP"
SOURCE_DETERMINISTIC_HUMANIZE = "DETERMINISTIC_HUMANIZE"
SOURCE_TECHNICAL_FALLBACK = "TECHNICAL_FALLBACK"
SOURCE_LLM_LOCALIZATION = "LLM_LOCALIZATION"

_MODE_ENV = "ACTION_DISPLAY_LABEL_MODE"


@dataclass(frozen=True)
class ActionDisplayLabelResult:
    label: str
    source: str
    shadow_label: str | None = None
    shadow_source: str | None = None


class ActionDisplayLabelResolver:
    """Cascata canônica (default): locale → summary PT → LLM/cache → humanize → id.

    Modos (`ACTION_DISPLAY_LABEL_MODE`):
    - ``legacy``: pathLabels primeiro (rollback temporário; EXIT = E1.S3)
    - ``shadow``: UX legacy; calcula candidato canônico para telemetria
    - ``default``: sem pathLabels; englishSummaries só como ponte até E1.S3
    """

    _llm_localizer: Callable[..., str | None] | None = None
    _cache_get: Callable[[str], str | None] | None = None
    _cache_put: Callable[[str, str, str], None] | None = None

    @classmethod
    def configure(
        cls,
        *,
        llm_localizer: Callable[..., str | None] | None = None,
        cache_get: Callable[[str], str | None] | None = None,
        cache_put: Callable[[str, str, str], None] | None = None,
    ) -> None:
        cls._llm_localizer = llm_localizer
        cls._cache_get = cache_get
        cls._cache_put = cache_put

    @classmethod
    def mode(cls) -> str:
        token = str(os.environ.get(_MODE_ENV) or "default").strip().lower()
        if token in {"legacy", "shadow", "default"}:
            return token
        return "default"

    @classmethod
    def resolve(
        cls,
        *,
        path: str,
        method: str,
        summary: str,
        action_id: str = "",
        provider_key: str = "",
        schema_hash: str = "",
        locale: str = "pt-BR",
        delpi_metadata: dict | None = None,
    ) -> ActionDisplayLabelResult:
        from app.domain.services.chat_action_label_service import ChatActionLabelService

        legacy = cls._resolve_legacy(
            path=path,
            method=method,
            summary=summary,
            action_id=action_id,
        )
        candidate = cls._resolve_canonical(
            path=path,
            method=method,
            summary=summary,
            action_id=action_id,
            provider_key=provider_key,
            schema_hash=schema_hash,
            locale=locale,
            delpi_metadata=delpi_metadata,
        )

        current_mode = cls.mode()

        if current_mode == "legacy":
            return ActionDisplayLabelResult(label=legacy.label, source=legacy.source)

        if current_mode == "shadow":
            if legacy.label != candidate.label or legacy.source != candidate.source:
                logger.info(
                    "action_display_label_shadow_diff",
                    extra={
                        "path": path,
                        "actionId": action_id,
                        "legacyLabel": legacy.label,
                        "legacySource": legacy.source,
                        "candidateLabel": candidate.label,
                        "candidateSource": candidate.source,
                    },
                )
                try:
                    from app.domain.services.catalog_display_observability_service import (
                        CatalogDisplayObservabilityService,
                    )

                    CatalogDisplayObservabilityService.record_action_label(
                        source=legacy.source,
                        path=path,
                        provider_key=provider_key,
                        shadow_diff=True,
                    )
                except Exception:
                    pass
            return ActionDisplayLabelResult(
                label=legacy.label,
                source=legacy.source,
                shadow_label=candidate.label,
                shadow_source=candidate.source,
            )

        try:
            from app.domain.services.catalog_display_observability_service import (
                CatalogDisplayObservabilityService,
            )

            CatalogDisplayObservabilityService.record_action_label(
                source=candidate.source,
                path=path,
                provider_key=provider_key,
                shadow_diff=False,
            )
        except Exception:
            pass

        return candidate

    @classmethod
    def _resolve_legacy(
        cls,
        *,
        path: str,
        method: str,
        summary: str,
        action_id: str,
    ) -> ActionDisplayLabelResult:
        from app.domain.services.chat_action_label_service import ChatActionLabelService

        path_label = ChatActionLabelService._label_from_path(path)
        if path_label:
            return ActionDisplayLabelResult(label=path_label, source=SOURCE_LEGACY_PATH_LABEL)

        return cls._resolve_after_path_label(
            path=path,
            method=method,
            summary=summary,
            action_id=action_id,
            prefer_summary_first=False,
        )

    @classmethod
    def _resolve_canonical(
        cls,
        *,
        path: str,
        method: str,
        summary: str,
        action_id: str,
        provider_key: str,
        schema_hash: str,
        locale: str,
        delpi_metadata: dict | None,
    ) -> ActionDisplayLabelResult:
        from app.domain.services.chat_action_label_service import ChatActionLabelService

        localized = cls._locale_summary(delpi_metadata, locale=locale)
        if localized and not ChatActionLabelService._looks_english(localized):
            return ActionDisplayLabelResult(
                label=localized,
                source=SOURCE_OPENAPI_LOCALIZED,
            )

        raw = str(summary or "").strip()

        if raw and not ChatActionLabelService._looks_english(raw):
            return ActionDisplayLabelResult(label=raw, source=SOURCE_OPENAPI_SUMMARY)

        if raw and ChatActionLabelService._looks_english(raw):
            cached = cls._try_cache_or_llm(
                path=path,
                method=method,
                summary=raw,
                action_id=action_id,
                provider_key=provider_key or "unknown",
                schema_hash=schema_hash,
                locale=locale,
            )
            if cached:
                return cached

        return cls._resolve_after_path_label(
            path=path,
            method=method,
            summary=summary,
            action_id=action_id,
            prefer_summary_first=False,
        )

    @classmethod
    def _resolve_after_path_label(
        cls,
        *,
        path: str,
        method: str,
        summary: str,
        action_id: str,
        prefer_summary_first: bool,
    ) -> ActionDisplayLabelResult:
        from app.domain.services.chat_action_label_service import (
            ChatActionLabelService,
            _default_authorized_query_label,
        )

        raw = str(summary or "").strip()

        if prefer_summary_first and raw and not ChatActionLabelService._looks_english(raw):
            return ActionDisplayLabelResult(label=raw, source=SOURCE_OPENAPI_SUMMARY)

        mapped = ChatActionLabelService._lookup_english_summary(raw)
        if mapped:
            return ActionDisplayLabelResult(
                label=mapped,
                source=SOURCE_ENGLISH_SUMMARY_MAP,
            )

        if raw and not ChatActionLabelService._looks_english(raw):
            return ActionDisplayLabelResult(label=raw, source=SOURCE_OPENAPI_SUMMARY)

        from_path = ChatActionLabelService._label_from_path_tail(path, method)
        if from_path:
            return ActionDisplayLabelResult(
                label=from_path,
                source=SOURCE_DETERMINISTIC_HUMANIZE,
            )

        translated = ChatActionLabelService._translate_english_summary(raw)
        if translated:
            return ActionDisplayLabelResult(
                label=translated,
                source=SOURCE_DETERMINISTIC_HUMANIZE,
            )

        if raw:
            return ActionDisplayLabelResult(label=raw, source=SOURCE_TECHNICAL_FALLBACK)

        fallback = action_id or path or _default_authorized_query_label()
        return ActionDisplayLabelResult(
            label=fallback,
            source=SOURCE_TECHNICAL_FALLBACK,
        )

    @classmethod
    def _locale_summary(cls, delpi_metadata: dict | None, *, locale: str) -> str | None:
        if not isinstance(delpi_metadata, dict):
            return None

        locale_node = delpi_metadata.get("locale")
        if not isinstance(locale_node, dict):
            return None

        block = locale_node.get(locale) or locale_node.get("pt-BR")
        if not isinstance(block, dict):
            return None

        for key in ("summary", "label"):
            value = block.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        return None

    @classmethod
    def cache_key(
        cls,
        *,
        provider_key: str,
        action_id: str,
        schema_hash: str,
        locale: str,
        localization_version: str = "1",
    ) -> str:
        raw = "|".join(
            [
                str(provider_key or "").strip(),
                str(action_id or "").strip(),
                str(schema_hash or "").strip(),
                str(locale or "pt-BR").strip(),
                str(localization_version).strip(),
            ]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def _try_cache_or_llm(
        cls,
        *,
        path: str,
        method: str,
        summary: str,
        action_id: str,
        provider_key: str,
        schema_hash: str,
        locale: str,
    ) -> ActionDisplayLabelResult | None:
        # Localization is universal: first-party EN without locale + external providers.
        key = cls.cache_key(
            provider_key=provider_key or "unknown",
            action_id=action_id or path,
            schema_hash=schema_hash,
            locale=locale,
        )

        if cls._cache_get:
            try:
                hit = cls._cache_get(key)
            except Exception:
                hit = None
            if isinstance(hit, str) and hit.strip():
                return ActionDisplayLabelResult(
                    label=hit.strip(),
                    source=SOURCE_LLM_LOCALIZATION,
                )

        if not cls._llm_localizer:
            return None

        try:
            localized = cls._llm_localizer(
                summary=summary,
                path=path,
                method=method,
                locale=locale,
            )
        except Exception:
            logger.debug("action_display_label_llm_failed", exc_info=True)
            return None

        if not isinstance(localized, str) or not localized.strip():
            return None

        label = localized.strip()
        if cls._cache_put:
            try:
                cls._cache_put(key, label, SOURCE_LLM_LOCALIZATION)
            except Exception:
                logger.debug("action_display_label_cache_put_failed", exc_info=True)

        return ActionDisplayLabelResult(label=label, source=SOURCE_LLM_LOCALIZATION)
