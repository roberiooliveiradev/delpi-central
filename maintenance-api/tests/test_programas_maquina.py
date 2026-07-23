from unittest.mock import MagicMock

from maint_app.application.services.programas_maquina_service import ProgramasMaquinaService
from maint_app.infrastructure.gateways.delpi_machine_programs_gateway import (
    DelpiMachineProgramsGateway,
)


def test_listar_top_intermediates_propaga_client(monkeypatch):
    client = MagicMock()
    client.list_production_machine_program_top_intermediates.return_value = {
        "items": [],
        "total": 0,
    }
    monkeypatch.setattr(
        "maint_app.infrastructure.gateways.delpi_machine_programs_gateway.bearer_authorization_from_context",
        lambda: "Bearer token",
    )

    gateway = DelpiMachineProgramsGateway(client)
    result = gateway.listar_top_intermediates(
        filial="01",
        page=1,
        page_size=50,
        search="502",
    )

    assert result["total"] == 0
    client.list_production_machine_program_top_intermediates.assert_called_once_with(
        params={
            "branch": "01",
            "page": "1",
            "page_size": "50",
            "date_start": None,
            "date_end": None,
            "search": "502",
        },
        authorization="Bearer token",
    )


def test_ranking_marks_already_registered():
    totvs = MagicMock()
    totvs.listar_top_intermediates.return_value = {
        "items": [
            {"intermediate_code": "50212155", "qty_produced": 10},
            {"intermediate_code": "50299999", "qty_produced": 5},
        ],
        "page": 1,
        "page_size": 50,
        "total": 2,
        "total_pages": 1,
        "summary": {},
    }
    repo = MagicMock()
    repo.list_active_codes.return_value = {"50212155"}

    service = ProgramasMaquinaService(totvs_gateway=totvs, produtos_repo=repo)
    data = service.ranking(filial="01")

    assert data["items"][0]["already_registered"] is True
    assert data["items"][1]["already_registered"] is False
    repo.list_active_codes.assert_called_once_with(filial="01")
