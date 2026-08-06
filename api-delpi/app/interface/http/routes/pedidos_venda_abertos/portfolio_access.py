from __future__ import annotations

from delpi_auth.authz_core import has_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    API_DELPI_ACCESS,
    COMMERCIAL_SELLER_PORTFOLIOS_MANAGE,
    PEDIDOS_VENDA_ABERTOS_ADMIN,
)


def current_user_id() -> str:
    user = get_current_user()
    return str(getattr(user, "id", "") or "").strip()


def is_portfolio_unrestricted() -> bool:
    """Gerente (.admin / commercial manage) ou acesso amplo api-delpi.access — vê todas as carteiras."""
    user = get_current_user()
    return (
        has_permission(user, PEDIDOS_VENDA_ABERTOS_ADMIN)
        or has_permission(user, COMMERCIAL_SELLER_PORTFOLIOS_MANAGE)
        or has_permission(user, API_DELPI_ACCESS)
    )


def is_portfolio_admin() -> bool:
    user = get_current_user()
    return (
        has_permission(user, PEDIDOS_VENDA_ABERTOS_ADMIN)
        or has_permission(user, COMMERCIAL_SELLER_PORTFOLIOS_MANAGE)
        or has_permission(user, API_DELPI_ACCESS)
    )
