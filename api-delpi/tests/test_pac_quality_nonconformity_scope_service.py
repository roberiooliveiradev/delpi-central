from __future__ import annotations

import pytest

from app.domain.services.quality_action_plans.pac_quality_nonconformity_scope_service import (
    validate_nonconformity_scope,
)


def test_validate_nonconformity_scope_accepts_internal_and_external():
    assert validate_nonconformity_scope("internal") == "internal"
    assert validate_nonconformity_scope("EXTERNAL") == "external"


def test_validate_nonconformity_scope_rejects_invalid():
    with pytest.raises(ValueError, match="nonconformity_scope inválido"):
        validate_nonconformity_scope("customer")


def test_validate_nonconformity_scope_requires_value_when_required():
    with pytest.raises(ValueError, match="obrigatório"):
        validate_nonconformity_scope(None)
