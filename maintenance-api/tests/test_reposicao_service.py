from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from maint_app.application.services.filial_access_scope_service import FilialAccessScope
from maint_app.application.services.reposicao_service import ReposicaoService


def test_validate_payload_rejects_non_positive_golpes():
    service = ReposicaoService(reposicao_repo=MagicMock())
    with pytest.raises(ValueError, match="Golpes"):
        service.validate_payload(
            {
                "filial": "01",
                "codigo_ferramenta": "23-001",
                "codigo_peca": "P001",
                "data_reposicao": datetime.now(timezone.utc).isoformat(),
                "golpes": 0,
                "motivo_id": 1,
            }
        )


def test_validate_payload_requires_date_after_last_replacement():
    repo = MagicMock()
    repo.get_ultima_data.return_value = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    service = ReposicaoService(reposicao_repo=repo)

    with pytest.raises(ValueError, match="posterior"):
        service.validate_payload(
            {
                "filial": "01",
                "codigo_ferramenta": "23-001",
                "codigo_peca": "P001",
                "data_reposicao": "2026-06-01T10:00:00+00:00",
                "golpes": 10,
                "motivo_id": 1,
            }
        )


def test_sugerir_golpes_usa_intervalo_datetime_no_totvs():
    repo = MagicMock()
    repo.get_ultima_data.return_value = datetime(2026, 6, 12, 10, 51, tzinfo=timezone.utc)
    totvs = MagicMock()
    totvs.obter_golpes.return_value = {"total_golpes": 42}
    service = ReposicaoService(reposicao_repo=repo, totvs_gateway=totvs)

    payload = service.sugerir_golpes(
        filial="01",
        codigo_ferramenta="23-001",
        codigo_peca="P001",
        data_inicial="2026-06-12T10:51:00",
        data_final="2026-06-12T11:04:00",
    )

    totvs.obter_golpes.assert_called_once_with(
        filial="01",
        codigo_ferramenta="23-001",
        data_inicial="2026-06-12T10:51:00",
        data_final="2026-06-12T11:04:00",
    )
    assert payload["total_golpes"] == 42


def test_create_checks_manage_permission():
    repo = MagicMock()
    repo.get_ultima_data.return_value = None
    repo.create.return_value = {"reposicao_id": "abc"}
    service = ReposicaoService(reposicao_repo=repo)
    scope = FilialAccessScope(mode="scoped", allowed_codigos=frozenset({"01"}), manage_codigos=frozenset())

    with pytest.raises(PermissionError):
        service.create(
            {
                "filial": "01",
                "codigo_ferramenta": "23-001",
                "codigo_peca": "P001",
                "data_reposicao": "2026-06-12T10:00:00+00:00",
                "golpes": 10,
                "motivo_id": 1,
            },
            scope=scope,
            user=MagicMock(is_superadmin=False, permissions=[]),
        )
