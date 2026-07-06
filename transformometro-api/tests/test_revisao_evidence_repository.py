from __future__ import annotations

from unittest.mock import MagicMock

from tm_app.infrastructure.persistence.repositories.revisao_evidence_repository import (
    RevisaoEvidenceRepository,
)


def test_create_returns_row():
    conn = MagicMock()
    repo = RevisaoEvidenceRepository(connection=conn)
    evidencia_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    revisao_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

    repo.execute_returning_one = MagicMock(return_value={"evidencia_id": evidencia_id})
    repo.get = MagicMock(
        return_value={
            "evidencia_id": evidencia_id,
            "revisao_id": revisao_id,
            "tipo": "documento",
            "nome_arquivo": "relatorio.pdf",
        }
    )

    row = repo.create(
        revisao_id,
        {
            "tipo": "documento",
            "nome_arquivo": "relatorio.pdf",
            "nome_armazenado": "abc.pdf",
            "tipo_mime": "application/pdf",
            "tamanho_bytes": 42,
        },
    )

    assert row["evidencia_id"] == evidencia_id
    repo.get.assert_called_once_with(revisao_id, evidencia_id)
