from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from tm_app.application.services.revisao_duplicate_service import (
    RevisaoDuplicateService,
    RevisaoNotFoundError,
)
from tm_app.application.services.revisao_version_utils import suggest_duplicate_versao_revisao


def test_suggest_duplicate_versao_revisao_bumps_patch() -> None:
    assert suggest_duplicate_versao_revisao("1.1.0", {"1.0.0", "1.1.0"}) == "1.1.1"


def test_suggest_duplicate_versao_revisao_skips_existing_patch() -> None:
    assert suggest_duplicate_versao_revisao("1.1.0", {"1.1.0", "1.1.1"}) == "1.1.2"


def test_suggest_duplicate_versao_revisao_fallback_for_non_semver() -> None:
    assert suggest_duplicate_versao_revisao("v1", {"v1"}) == "v1-copia-2"


@patch("tm_app.application.services.revisao_duplicate_service.get_plugins_connection")
@patch("tm_app.application.services.revisao_duplicate_service.RevisaoEvidenceStorage")
@patch("tm_app.application.services.revisao_duplicate_service.RevisaoEvidenceRepository")
@patch("tm_app.application.services.revisao_duplicate_service.RevisaoDecomposicaoOverlayRepository")
@patch("tm_app.application.services.revisao_duplicate_service.RevisaoDiagramOverlayRepository")
@patch("tm_app.application.services.revisao_duplicate_service.VinculoRepository")
@patch("tm_app.application.services.revisao_duplicate_service.InvestimentoRepository")
@patch("tm_app.application.services.revisao_duplicate_service.MedicaoRepository")
@patch("tm_app.application.services.revisao_duplicate_service.RevisaoRepository")
def test_duplicate_revisao_creates_inactive_copy(
    mock_rev_cls,
    mock_med_cls,
    mock_inv_cls,
    mock_vin_cls,
    mock_diagram_cls,
    mock_decomp_cls,
    mock_evidence_cls,
    mock_storage_cls,
    mock_conn_factory,
):
    conn = MagicMock()
    mock_conn_factory.return_value = conn

    rev_repo = mock_rev_cls.return_value
    med_repo = mock_med_cls.return_value
    inv_repo = mock_inv_cls.return_value
    vin_repo = mock_vin_cls.return_value
    rev_diagram_repo = mock_diagram_cls.return_value
    rev_decomp_repo = mock_decomp_cls.return_value
    evidence_repo = mock_evidence_cls.return_value

    rev_repo.get.side_effect = lambda rid: (
        {
            "revisao_id": "r-new",
            "processo_id": "p1",
            "instancia_id": "i1",
            "versao_revisao": "1.1.1",
            "cenario_tipo": "melhoria",
            "data_inicio_vigencia": "2025-01-01",
            "revisao_referencia_id": "r-base",
        }
        if rid == "r-new"
        else {
            "revisao_id": "r-src",
            "processo_id": "p1",
            "instancia_id": "i1",
            "versao_revisao": "1.1.0",
            "cenario_tipo": "melhoria",
            "data_inicio_vigencia": "2025-01-01",
            "revisao_referencia_id": "r-base",
            "revisao_ativa": True,
            "matriz_impacto_esforco": {"format": "revisao_matriz_impacto_esforco_v1"},
        }
    )
    rev_repo.list_by_instancia.return_value = [
        {"versao_revisao": "1.0.0"},
        {"versao_revisao": "1.1.0"},
    ]
    rev_repo.create.return_value = {
        "revisao_id": "r-new",
        "processo_id": "p1",
        "instancia_id": "i1",
        "versao_revisao": "1.1.1",
    }
    med_repo.get_by_revisao.return_value = None
    inv_repo.list_by_revisao.return_value = []
    vin_repo.list_by_revisao.return_value = []
    rev_diagram_repo.get.return_value = None
    rev_decomp_repo.get.return_value = None
    evidence_repo.list_by_revisao.return_value = []

    result = RevisaoDuplicateService().duplicate("r-src")

    assert result["revisao"]["revisao_id"] == "r-new"
    assert result["copiados"]["revisoes"] == 1
    assert result["copiados"]["matriz_impacto_esforco"] == 1
    create_payload = rev_repo.create.call_args[0][0]
    assert create_payload["versao_revisao"] == "1.1.1"
    assert create_payload["revisao_ativa"] is False
    assert create_payload["revisao_referencia_id"] == "r-base"
    conn.commit.assert_called_once()


@patch("tm_app.application.services.revisao_duplicate_service.get_plugins_connection")
@patch("tm_app.application.services.revisao_duplicate_service.RevisaoRepository")
def test_duplicate_revisao_not_found(mock_rev_cls, mock_conn_factory):
    mock_conn_factory.return_value = MagicMock()
    mock_rev_cls.return_value.get.return_value = None
    with pytest.raises(RevisaoNotFoundError):
        RevisaoDuplicateService().duplicate("missing")
