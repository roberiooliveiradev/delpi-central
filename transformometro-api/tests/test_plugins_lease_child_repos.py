"""Regressão: repos não exigem lease ao encadear filhos após fetch_*."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tm_app.infrastructure.persistence.repositories.process_repository import (
    ProcessoRepository,
)
from tm_app.infrastructure.persistence.repositories.resource_cost_repository import (
    RecursoCustoRepository,
)


def test_processo_enrich_without_active_lease_does_not_touch_connection_property():
    repo = ProcessoRepository()
    row = {"processo_id": "p1", "nome_processo": "X"}
    with patch(
        "tm_app.infrastructure.persistence.repositories.process_repository.ProcessoEscopoRepository"
    ) as escopo_cls:
        escopo = MagicMock()
        escopo.enrich_row.side_effect = lambda r: {**r, "filial_ids": []}
        escopo_cls.return_value = escopo
        out = repo._enrich_row(row)
        escopo_cls.assert_called_once_with(connection=None)
        assert out["processo_id"] == "p1"


def test_sync_valor_atual_uses_injected_or_none_not_lease_property():
    repo = RecursoCustoRepository()
    with (
        patch.object(
            repo,
            "fetch_one",
            return_value={"valor_mensal": 10.5},
        ),
        patch(
            "tm_app.infrastructure.persistence.repositories.resource_cost_repository.RecursoRepository"
        ) as recurso_cls,
    ):
        recurso = MagicMock()
        recurso.get.return_value = {"recurso_id": "r1", "nome": "A"}
        recurso_cls.return_value = recurso
        repo.sync_valor_atual("r1")
        recurso_cls.assert_called_with(connection=None)
        recurso.update.assert_called_once()
