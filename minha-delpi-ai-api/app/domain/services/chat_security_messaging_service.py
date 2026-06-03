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

        if "/system/" in lowered_path:
            lowered_error = error.lower()

            if any(
                term in lowered_error
                for term in (
                    "banco de dados",
                    "banco",
                    "timeout",
                    "conexão",
                    "conexao",
                    "connection",
                    "sql server",
                    "sqldriverconnect",
                )
            ):
                return ExternalActionResponseContentService.get(
                    "security",
                    "systemMetadataQueryFailed",
                )

        if "/data/sql" in lowered_path:
            from app.domain.services.chat_sql_execution_error_interpretation_service import (
                ChatSqlExecutionErrorInterpretationService,
            )

            friendly = ChatSqlExecutionErrorInterpretationService.user_facing_message(
                error,
                path=lowered_path,
            )

            if friendly:
                return friendly

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
            if "/data/sql" in lowered_path:
                from app.domain.services.chat_sql_execution_error_interpretation_service import (
                    ChatSqlExecutionErrorInterpretationService,
                )

                if ChatSqlExecutionErrorInterpretationService.is_raw_driver_dump(error):
                    return ExternalActionResponseContentService.get(
                        "security",
                        "operationalQueryFailed",
                    )

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
