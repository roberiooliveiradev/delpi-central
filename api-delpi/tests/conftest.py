"""Fixtures compartilhadas para testes da api-delpi."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def authenticated_superadmin():
    """Bypass de require_permission nos testes que chamam handlers diretamente."""
    user = MagicMock()
    user.id = "11111111-1111-4111-8111-111111111111"
    user.is_superadmin = True

    with patch("delpi_auth.authorization.resolve_user_context", return_value=user):
        yield user
