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

        lowered_error = error.lower()

        if "/stock" in lowered_path or "estoque" in lowered_error:
            return ExternalActionResponseContentService.get(
                "security",
                "stockQueryFailed",
            )

        if "/system/" in lowered_path:
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

        if code == 504 or cls._looks_like_http_read_timeout(error):
            return ExternalActionResponseContentService.get(
                "composite",
                "timeout",
            )

        if code in (401, 403) or lowered_error in ("unauthorized", "forbidden"):
            return ExternalActionResponseContentService.get(
                "security",
                "noAccess",
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

        if error and cls._looks_like_internal_error(error):
            return cls._resolve_internal_error_message(lowered_path)

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
    def _looks_like_http_read_timeout(cls, error: str) -> bool:
        lowered = str(error or "").strip().lower()

        if not lowered:
            return False

        return (
            lowered == "timeout"
            or "read timed out" in lowered
            or "readtimeout" in lowered.replace(" ", "")
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

    @classmethod
    def _looks_like_internal_error(cls, error: str) -> bool:
        lowered = str(error or "").strip().lower()

        if not lowered:
            return False

        if cls._looks_like_technical_only(lowered):
            return True

        internal_markers = (
            "has no attribute",
            "type object",
            "traceback",
            "attributeerror",
            "keyerror",
            "typeerror",
            "valueerror",
            "nameerror",
            "importerror",
            "modulenotfounderror",
            "exception:",
            "  file ",
            "line ",
        )

        return any(marker in lowered for marker in internal_markers)

    @classmethod
    def _resolve_internal_error_message(cls, lowered_path: str) -> str:
        if "/structure" in lowered_path and "/analyser" not in lowered_path:
            return ExternalActionResponseContentService.get(
                "security",
                "structurePresentationFailed",
            )

        return ExternalActionResponseContentService.get(
            "security",
            "presentationFormatFailed",
        )
