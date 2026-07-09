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
    with pytest.raises(ValueError, match="codigo_setor inválido"):
        normalize_setor_id("   ")


def test_create_uses_normalized_codigo_and_syncs_filiais():
    conn = MagicMock()
    repo = SetorRepository(connection=conn)
    setor_uuid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    repo.get = MagicMock(
        side_effect=[
            None,
            {"setor_id": setor_uuid, "codigo_setor": "comercial", "filiais": ["01"]},
        ]
    )
    repo._validate_filiais = MagicMock()
    repo.execute_returning_one = MagicMock(
        return_value={
            "setor_id": setor_uuid,
            "codigo_setor": "comercial",
            "nome_setor": "Comercial",
        }
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

    assert row["codigo_setor"] == "comercial"
    insert_sql = repo.execute_returning_one.call_args[0][0]
    assert "gen_random_uuid()" in insert_sql
    repo._sync_filiais.assert_called_once_with(setor_uuid, ["01"], auto_commit=True)


def test_list_for_options_exposes_uuid_and_codigo():
    repo = SetorRepository(connection=MagicMock())
    setor_uuid = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    repo.list = MagicMock(
        return_value=[
            {
                "setor_id": setor_uuid,
                "codigo_setor": "engenharia",
                "nome_setor": "Engenharia",
                "status_setor": "ativo",
                "filiais": ["01", "02"],
            }
        ]
    )

    options = repo.list_for_options()
    assert options[0]["id"] == "engenharia"
    assert options[0]["setor_id"] == setor_uuid
    assert options[0]["filiais"] == ["01", "02"]


def test_soft_delete_blocks_when_processos_exist():
    repo = SetorRepository(connection=MagicMock())
    repo.count_processos = MagicMock(return_value=2)

    with pytest.raises(ValueError, match="vinculado a processos"):
        repo.soft_delete("comercial")


def test_update_allows_codigo_setor_rename():
    conn = MagicMock()
    repo = SetorRepository(connection=conn)
    setor_uuid = "cccccccc-cccc-cccc-cccc-cccccccccccc"
    repo.get = MagicMock(
        side_effect=[
            {
                "setor_id": setor_uuid,
                "codigo_setor": "suprimentos",
                "nome_setor": "Suprimentos",
                "filiais": ["01"],
            },
            None,
            {
                "setor_id": setor_uuid,
                "codigo_setor": "supplies",
                "nome_setor": "Suprimentos",
                "filiais": ["01"],
            },
        ]
    )
    repo._validate_filiais = MagicMock()
    repo.execute_returning_one = MagicMock(return_value={"setor_id": setor_uuid})
    repo.execute = MagicMock()
    repo._sync_filiais = MagicMock()

    updated = repo.update(
        setor_uuid,
        {
            "codigo_setor": "supplies",
            "nome_setor": "Suprimentos",
            "filiais": ["01"],
            "status_setor": "ativo",
        },
    )

    assert updated["codigo_setor"] == "supplies"
    update_sql = repo.execute_returning_one.call_args[0][0]
    assert "codigo_setor = %s" in update_sql
    repo.execute.assert_called_once()
    assert "dashboard_calculos" in repo.execute.call_args[0][0]
