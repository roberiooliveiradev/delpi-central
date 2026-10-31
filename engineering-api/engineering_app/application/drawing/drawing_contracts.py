"""Delegated-contract normalization for drawing analysis (R1).

The delegated auxiliary gateway answers `{"status", "data"}` (or a
typed error status). Unwrapping lives here — never as ad-hoc checks in
the domain. A denied or unavailable source must NEVER degrade into
`drawing_not_found`.
"""

from __future__ import annotations

from typing import Any


class DrawingAnalysisError(RuntimeError):
    """Analysis could not proceed; carries a stable error code."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


_ERROR_STATUSES = {"not_found", "forbidden", "unavailable", "error"}


def unwrap_delegated(
    payload: Any,
    *,
    what: str,
    not_found_code: str,
    not_found_message: str,
    not_found_status: int = 404,
) -> dict[str, Any]:
    """Return the inner data dict of a delegated envelope or raise.

    Accepts both the canonical envelope ``{"status","data"}`` and raw
    data dicts (tests/legacy). Error statuses map to typed, honest
    errors — permission failures keep 403 semantics.
    """
    if not isinstance(payload, dict):
        raise DrawingAnalysisError(
            "source_unavailable", f"{what}: resposta inválida da fonte.", 502
        )
    status = payload.get("status")
    if "data" in payload and status in (None, "available", "ok"):
        data = payload["data"]
        if isinstance(data, dict):
            return data
        raise DrawingAnalysisError(
            "source_unavailable", f"{what}: payload 'data' inválido.", 502
        )
    if status in _ERROR_STATUSES:
        if status == "forbidden":
            raise DrawingAnalysisError(
                "forbidden",
                f"{what}: acesso negado — permissão insuficiente na "
                "fonte oficial (não confundir com ausência).",
                403,
            )
        if status == "not_found":
            raise DrawingAnalysisError(
                not_found_code, not_found_message, not_found_status
            )
        raise DrawingAnalysisError(
            "source_unavailable",
            f"{what}: fonte oficial temporariamente indisponível "
            f"({payload.get('reason') or status}).",
            502,
        )
    # Raw data dict (no envelope) — return as-is.
    return payload
