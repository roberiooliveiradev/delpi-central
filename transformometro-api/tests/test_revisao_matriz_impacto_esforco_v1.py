import pytest

from tm_app.domain.matrix.revisao_matriz_impacto_esforco_v1 import (
    MatrizImpactoEsforcoValidationError,
    build_persisted_matriz_payload,
    validate_revisao_matriz_impacto_esforco_v1,
)


def test_build_persisted_payload_defaults_auto():
    doc = build_persisted_matriz_payload({"modo": "auto"}, atualizado_por="user@test.com")
    assert doc["format"] == "revisao_matriz_impacto_esforco_v1"
    assert doc["modo"] == "auto"
    assert doc["atualizado_por"] == "user@test.com"
    assert "atualizado_em" in doc


def test_validate_inputs_manuais_scale_range():
    with pytest.raises(MatrizImpactoEsforcoValidationError):
        build_persisted_matriz_payload(
            {"modo": "manual", "inputs_manuais": {"impacto_qualitativo": 6}},
            atualizado_por="u",
        )


def test_validate_overrides_bounds():
    with pytest.raises(MatrizImpactoEsforcoValidationError):
        build_persisted_matriz_payload(
            {"modo": "hibrido", "overrides": {"impacto": 120}},
            atualizado_por="u",
        )


def test_validate_full_document_accepts_hibrido():
    doc = validate_revisao_matriz_impacto_esforco_v1(
        {
            "format": "revisao_matriz_impacto_esforco_v1",
            "format_version": 1,
            "modo": "hibrido",
            "inputs_manuais": {
                "impacto_qualitativo": 4,
                "esforco_qualitativo": 3,
                "observacao": "Piloto Q3",
            },
            "overrides": {"impacto": None, "esforco": 42.5},
            "atualizado_em": "2026-07-08T12:00:00+00:00",
            "atualizado_por": "ana@delpi.local",
        }
    )
    assert doc["modo"] == "hibrido"
    assert doc["overrides"]["esforco"] == 42.5
