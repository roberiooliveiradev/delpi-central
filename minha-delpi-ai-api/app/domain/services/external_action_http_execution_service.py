"""Política HTTP para actions externas — timeout e retry (Playbook qualidade operacional S1)."""

from __future__ import annotations

from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionHttpExecutionService:
    @classmethod
    def default_timeout_seconds(cls) -> int:
        return cls._int_setting("defaultTimeoutSeconds", 30, minimum=5)

    @classmethod
    def composite_analysis_timeout_seconds(cls) -> int:
        return cls._int_setting("compositeAnalysisTimeoutSeconds", 60, minimum=5)

    @classmethod
    def retry_once_on_timeout(cls) -> bool:
        return cls._bool_setting("retryOnceOnTimeout", True)

    @classmethod
    def retry_status_codes(cls) -> frozenset[int]:
        node = ExternalActionResponseContentService.get_node("httpExecution", "retryOnceOnStatusCodes")

        if isinstance(node, list):
            codes = []

            for item in node:
                try:
                    codes.append(int(item))
                except (TypeError, ValueError):
                    continue

            if codes:
                return frozenset(codes)

        return frozenset({502, 503, 504})

    @classmethod
    def composite_path_markers(cls) -> tuple[str, ...]:
        node = ExternalActionResponseContentService.get_node("httpExecution", "compositePathMarkers")

        if isinstance(node, list):
            markers = tuple(
                str(item).strip().lower()
                for item in node
                if str(item).strip()
            )

            if markers:
                return markers

        return (
            "/factory-status",
            "/raw-material-price-intelligence",
            "/cost-impact-simulation",
            "/analyser",
        )

    @classmethod
    def resolve_timeout_seconds(
        cls,
        *,
        provider: dict | None,
        action_path: str = "",
    ) -> int:
        if isinstance(provider, dict):
            raw = provider.get("timeoutSeconds")

            try:
                provider_timeout = int(raw)

                if provider_timeout >= 5:
                    return provider_timeout
            except (TypeError, ValueError):
                pass

        lowered = str(action_path or "").strip().lower()

        if lowered and any(marker in lowered for marker in cls.composite_path_markers()):
            return cls.composite_analysis_timeout_seconds()

        return cls.default_timeout_seconds()

    @classmethod
    def should_retry(
        cls,
        *,
        attempt_index: int,
        status_code: int | None = None,
        timed_out: bool = False,
    ) -> bool:
        if attempt_index >= 1:
            return False

        if timed_out and cls.retry_once_on_timeout():
            return True

        if status_code is not None and int(status_code) in cls.retry_status_codes():
            return True

        return False

    @classmethod
    def _int_setting(cls, key: str, default: int, *, minimum: int) -> int:
        raw = ExternalActionResponseContentService.get("httpExecution", key, default=str(default))

        try:
            return max(minimum, int(raw))
        except (TypeError, ValueError):
            return max(minimum, default)

    @classmethod
    def _bool_setting(cls, key: str, default: bool) -> bool:
        node = ExternalActionResponseContentService.get_node("httpExecution", key)

        if isinstance(node, bool):
            return node

        return default
