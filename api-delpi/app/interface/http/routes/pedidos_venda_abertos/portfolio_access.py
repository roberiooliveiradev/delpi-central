from __future__ import annotations

from delpi_auth.authz_core import has_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import COMMERCIAL_MANAGE


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
    """commercial.manage — vê todas as carteiras sem filtro de membership."""
    user = get_current_user()
    return has_permission(user, COMMERCIAL_MANAGE)


def can_filter_by_seller_id() -> bool:
    """Filtro seller_id / todas as carteiras — somente manage."""
    return is_portfolio_unrestricted()


def is_portfolio_admin() -> bool:
    user = get_current_user()
    return has_permission(user, COMMERCIAL_MANAGE)
