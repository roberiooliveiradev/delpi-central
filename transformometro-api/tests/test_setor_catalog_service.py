from __future__ import annotations

import pytest

from tm_app.domain.services.setor_catalog_service import normalize_codigo_setor


def test_normalize_codigo_setor_slug():
    assert normalize_codigo_setor("Comercial") == "comercial"
    assert normalize_codigo_setor("  PCP & Logística ") == "pcp_log_stica"


def test_normalize_codigo_setor_rejects_empty():
    with pytest.raises(ValueError, match="codigo_setor inválido"):
        normalize_codigo_setor("   ")
