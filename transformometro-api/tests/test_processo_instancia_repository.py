from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tm_app.domain.services.processo_instancia_service import ProcessoInstanciaDomainError
from tm_app.infrastructure.persistence.repositories.processo_instancia_repository import (
    ProcessoInstanciaRepository,
)


def test_create_rejects_setor_not_linked_to_filial(monkeypatch):
    repo = ProcessoInstanciaRepository(connection=MagicMock())
    repo.fetch_one = MagicMock(return_value=None)

    processo_repo = MagicMock()
    processo_repo.get.return_value = {
        "processo_id": "11111111-1111-1111-1111-111111111111",
        "filial_id": "01",
        "setor_id": "engenharia",
    }
    setor_repo = MagicMock()
    setor_repo.is_active_for_filial.return_value = False

    monkeypatch.setattr(
        "tm_app.infrastructure.persistence.repositories.processo_instancia_repository.ProcessoRepository",
        lambda connection=None: processo_repo,
    )
    monkeypatch.setattr(
        "tm_app.infrastructure.persistence.repositories.processo_instancia_repository.SetorRepository",
        lambda connection=None: setor_repo,
    )

    with pytest.raises(ProcessoInstanciaDomainError, match="não está vinculado"):
        repo.create(
            {
                "processo_id": "11111111-1111-1111-1111-111111111111",
                "filial_id": "01",
                "setor_ids": ["engenharia"],
            }
        )


def test_get_by_processo_returns_first_row():
    repo = ProcessoInstanciaRepository(connection=MagicMock())
    instancia = {"instancia_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}
    repo.list_by_processo = MagicMock(return_value=[instancia])

    assert repo.get_by_processo("11111111-1111-1111-1111-111111111111") == instancia


def test_soft_delete_rejects_when_revisoes_exist():
    repo = ProcessoInstanciaRepository(connection=MagicMock())
    repo.get = MagicMock(
        return_value={
            "instancia_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "codigo_filial": "01",
        }
    )
    repo.count_revisoes = MagicMock(return_value=2)

    with pytest.raises(ProcessoInstanciaDomainError, match="revisões"):
        repo.soft_delete("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", auto_commit=False)


def test_update_requires_existing_instancia():
    repo = ProcessoInstanciaRepository(connection=MagicMock())
    repo.get = MagicMock(return_value=None)

    with pytest.raises(ProcessoInstanciaDomainError, match="não encontrada"):
        repo.update(
            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            {"setor_ids": ["engenharia"]},
            auto_commit=False,
        )
