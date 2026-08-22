from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from financial_app.application.services.response_cache import clear_cache
from financial_app.core.security import (
    FIN_ACCESS,
    FIN_COST_CENTERS_VIEW,
    FIN_DELINQUENCY_VIEW,
    FIN_INDICATORS_VIEW,
    FIN_VIEW_FILIAL_01,
    FIN_VIEW_FILIAL_02,
)

ALL_PERMISSIONS = [
    FIN_ACCESS,
    FIN_DELINQUENCY_VIEW,
    FIN_COST_CENTERS_VIEW,
    FIN_INDICATORS_VIEW,
    FIN_VIEW_FILIAL_01,
    FIN_VIEW_FILIAL_02,
]


def user(*permissions: str, superadmin: bool = False) -> SimpleNamespace:
    return SimpleNamespace(is_superadmin=superadmin, permissions=list(permissions))


def full_user() -> SimpleNamespace:
    return user(*ALL_PERMISSIONS)


def envelope(data: Any) -> dict[str, Any]:
    """Resposta da api-delpi no formato `{success, message, data}`."""
    return {"success": True, "message": "OK", "data": data}


@pytest.fixture(autouse=True)
def reset_response_cache():
    clear_cache()
    yield
    clear_cache()
