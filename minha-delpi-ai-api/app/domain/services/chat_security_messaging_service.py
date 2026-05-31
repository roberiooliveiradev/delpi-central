"""Mensagens de segurança e confiança — Playbook 08 (chat base)."""

from __future__ import annotations

from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ChatSecurityMessagingService:
    @classmethod
    def resolve_api_failure(cls, metadata: dict | None, *, path: str = "") -> str:
        meta = metadata or {}
        status_code = meta.get("statusCode") or meta.get("status_code")
        error = str(meta.get("error") or meta.get("errorMessage") or meta.get("detail") or "").strip()
        lowered_path = str(path or meta.get("path") or "").lower()

        try:
            code = int(status_code)
        except (TypeError, ValueError):
            code = None

        if code == 404:
            return ExternalActionResponseContentService.get(
                "composite",
                "notFound404",
                default="Não encontrei esse recurso. Verifique o código ou filtro informado.",
            )

        if code in (401, 403) or error.lower() in ("unauthorized", "forbidden"):
            return ExternalActionResponseContentService.get(
                "security",
                "noAccess",
            )

        if "/stock" in lowered_path or "estoque" in error.lower():
            return ExternalActionResponseContentService.get(
                "security",
                "stockQueryFailed",
            )

        if code is not None and code >= 500:
            return ExternalActionResponseContentService.get(
                "security",
                "operationalQueryFailed",
                default=ExternalActionResponseContentService.format(
                    "composite",
                    "serverError",
                    code=code,
                ),
            )

        if error and not cls._looks_like_technical_only(error):
            return error

        if code is not None:
            return ExternalActionResponseContentService.get(
                "security",
                "operationalQueryFailed",
            )

        return ExternalActionResponseContentService.get(
            "security",
            "operationalQueryFailed",
        )

    @classmethod
    def _looks_like_technical_only(cls, error: str) -> bool:
        lowered = error.lower()

        return lowered in (
            "not found",
            "internal server error",
            "bad request",
            "service unavailable",
        )
