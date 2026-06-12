from __future__ import annotations

import pytest

from tm_app.domain.services.filial_catalog_service import (
    assert_filial_ativa,
    normalize_codigo_filial,
    validate_codigos_filiais,
)


def test_normalize_codigo_filial_accepts_business_codes():
    assert normalize_codigo_filial("01") == "01"
    assert normalize_codigo_filial(" matriz-sp ") == "matriz-sp"


def test_normalize_codigo_filial_rejects_invalid():
    with pytest.raises(ValueError, match="codigo_filial inválido"):
        normalize_codigo_filial("  ")


def test_validate_codigos_filiais_requires_at_least_one():
    with pytest.raises(ValueError, match="Informe ao menos uma filial"):
        validate_codigos_filiais([], {"01"})


def test_validate_codigos_filiais_reports_invalid():
    with pytest.raises(ValueError, match="filial_id inválido: 99"):
        validate_codigos_filiais(["01", "99"], {"01", "02"})


def test_assert_filial_ativa():
    assert_filial_ativa("01", {"01", "02"})
    with pytest.raises(ValueError, match="filial_id inválido"):
        assert_filial_ativa("99", {"01"})
