"""Formata falhas de fetch operacional para o `resolved` dos blocos de dados."""

from __future__ import annotations

from typing import Any

from delpi_api_client.client import DelpiApiError

from tv_app.application.services.tv_dashboard_content_service import message


def resolve_data_fetch_error(exc: BaseException) -> dict[str, Any]:
    """
    Mensagem para o editor/TV: prioriza o texto da api-delpi (status + detail),
    em vez de só «Dados indisponíveis no momento.».
    """
    fallback = message("nativeDataUnavailable", "Dados indisponíveis no momento.")
    status_code: int | None = None
    detail = str(exc).strip()

    if isinstance(exc, DelpiApiError):
        status_code = int(exc.status_code)
        detail = (exc.detail or "").strip() or detail
        display = f"[{status_code}] {detail}" if detail else f"[{status_code}] {fallback}"
    elif isinstance(exc, ValueError):
        display = detail or fallback
    else:
        display = detail or fallback

    if not display:
        display = fallback

    payload: dict[str, Any] = {
        "error": display,
        "detail": detail or display,
    }
    if status_code is not None:
        payload["statusCode"] = status_code
    return payload
