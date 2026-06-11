from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tm_app.infrastructure.persistence.repositories.setor_repository import (
    SetorRepository,
    normalize_setor_id,
)


def test_normalize_setor_id_slug():
    assert normalize_setor_id("Comercial") == "comercial"
    assert normalize_setor_id("  PCP & Logística ") == "pcp_log_stica"


def test_normalize_setor_id_rejects_empty():
    with pytest.raises(ValueError, match="setor_id inválido"):
        normalize_setor_id("   ")


def test_create_uses_normalized_id_and_syncs_filiais():
    conn = MagicMock()
    repo = SetorRepository(connection=conn)
    repo.get = MagicMock(side_effect=[None, {"setor_id": "comercial", "filiais": ["01"]}])
    repo._validate_filiais = MagicMock()
    repo.execute_returning_one = MagicMock(
        return_value={"setor_id": "comercial", "nome_setor": "Comercial"}
    )
    repo._sync_filiais = MagicMock()

    row = repo.create(
        {
            "setor_id": "Comercial",
            "nome_setor": "Comercial",
            "filiais": ["01"],
            "status_setor": "ativo",
        }
    )

    assert row["setor_id"] == "comercial"
    repo._sync_filiais.assert_called_once_with("comercial", ["01"], auto_commit=True)


def test_soft_delete_blocks_when_processos_exist():
    repo = SetorRepository(connection=MagicMock())
    repo.count_processos = MagicMock(return_value=2)

    with pytest.raises(ValueError, match="vinculado a processos"):
        repo.soft_delete("comercial")
