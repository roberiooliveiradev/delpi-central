"""Fixtures compartilhadas para testes da api-delpi."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

try:
    import pyodbc  # noqa: F401
except (ImportError, OSError):
    sys.modules.setdefault("pyodbc", MagicMock())


@pytest.fixture(autouse=True)
def authenticated_superadmin():
    """Bypass de require_permission nos testes que chamam handlers diretamente."""
    user = MagicMock()
    user.id = "11111111-1111-4111-8111-111111111111"
    user.is_superadmin = True

    with patch("delpi_auth.authorization.resolve_user_context", return_value=user):
        yield user
