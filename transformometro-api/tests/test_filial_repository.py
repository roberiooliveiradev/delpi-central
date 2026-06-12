from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from tm_app.infrastructure.persistence.repositories.filial_repository import FilialRepository


def test_create_normalizes_codigo_and_rejects_duplicate():
    conn = MagicMock()
    repo = FilialRepository(connection=conn)
    repo.get = MagicMock(side_effect=[None, {"filial_id": uuid4(), "codigo_filial": "01"}])
    repo.execute_returning_one = MagicMock(
        return_value={
            "filial_id": uuid4(),
            "codigo_filial": "01",
            "nome_filial": "Matriz",
            "status_filial": "ativo",
        }
    )

    row = repo.create(
        {"codigo_filial": " 01 ", "nome_filial": "Matriz", "status_filial": "ativo"}
    )
    assert row["codigo_filial"] == "01"
    repo.get.assert_called()


def test_soft_delete_blocks_when_processos_exist():
    filial_id = uuid4()
    repo = FilialRepository(connection=MagicMock())
    repo.get = MagicMock(return_value={"filial_id": filial_id, "codigo_filial": "01"})
    repo.count_processos = MagicMock(return_value=3)
    repo.count_setor_vinculos = MagicMock(return_value=0)

    with pytest.raises(ValueError, match="vinculada a processos"):
        repo.soft_delete(str(filial_id))


def test_list_for_options_keeps_codigo_as_id_for_mfe_compat():
    repo = FilialRepository(connection=MagicMock())
    filial_uuid = uuid4()
    repo.list = MagicMock(
        return_value=[
            {
                "filial_id": filial_uuid,
                "codigo_filial": "01",
                "nome_filial": "Matriz",
                "status_filial": "ativo",
            }
        ]
    )

    options = repo.list_for_options()
    assert options[0]["id"] == "01"
    assert options[0]["filial_id"] == filial_uuid
    assert options[0]["label"] == "Matriz"
