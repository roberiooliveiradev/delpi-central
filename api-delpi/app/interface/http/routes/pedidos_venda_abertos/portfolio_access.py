from __future__ import annotations

from delpi_auth.authz_core import has_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    COMMERCIAL_ACCOUNTS_TEAM_VIEW,
    COMMERCIAL_SELLER_PORTFOLIOS_MANAGE,
)


def current_user_id() -> str:
    user = get_current_user()
    if user is None:
        return ""
    for key in ("id", "sub", "user_id"):
        value = getattr(user, key, None)
        if value:
            return str(value).strip()
    return ""


def is_portfolio_unrestricted() -> bool:
    """manage ou team.view — consolidado sem membership (alinhado commercial-api)."""
    user = get_current_user()
    return has_permission(user, COMMERCIAL_SELLER_PORTFOLIOS_MANAGE) or has_permission(
        user, COMMERCIAL_ACCOUNTS_TEAM_VIEW
    )


def can_filter_by_seller_id() -> bool:
    """team.view ou manage — permite query seller_id nos pedidos em aberto."""
    return is_portfolio_unrestricted()


def is_portfolio_admin() -> bool:
    user = get_current_user()
    return has_permission(user, COMMERCIAL_SELLER_PORTFOLIOS_MANAGE)
