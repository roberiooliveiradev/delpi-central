"""Status HTTP repassado quando a api-delpi falha atrás do BFF."""

from __future__ import annotations

from production_control_app.domain.errors import DelpiGatewayError


def status_from_gateway_error(exc: DelpiGatewayError) -> int:
    """Preserva 4xx/5xx da api-delpi. Sem status upstream, o BFF responde 502."""
    upstream = exc.status_code if isinstance(exc.status_code, int) else None
    if upstream is not None and 400 <= upstream < 600:
        return upstream
    return 502
