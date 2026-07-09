from __future__ import annotations

from unittest.mock import MagicMock

from tm_app.infrastructure.persistence.repositories.processo_escopo_repository import (
    ProcessoEscopoRepository,
)


def test_save_escopo_commits_with_connection():
    conn = MagicMock()
    repo = ProcessoEscopoRepository(connection=conn)
    processo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    setor_uuid = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    repo.fetch_one = MagicMock(return_value={"todas_filiais_ativas": False})
    repo.fetch_all = MagicMock(return_value=[])
    repo._resolve_filiais = MagicMock(return_value=[])
    repo._resolve_setores = MagicMock(
        return_value=[{"setor_id": setor_uuid, "codigo_setor": "comercial"}]
    )
    repo.execute = MagicMock()
    repo.get_escopo = MagicMock(
        return_value={
            "todas_filiais_ativas": True,
            "filial_ids": [],
            "setor_ids": ["comercial"],
            "filiais": [],
            "setores": [],
        }
    )

    repo.save_escopo(
        processo_id,
        todas_filiais_ativas=True,
        filial_ids=[],
        setor_ids=["comercial"],
        auto_commit=True,
    )

    conn.commit.assert_called_once()
    repo.get_escopo.assert_called_once_with(processo_id)
