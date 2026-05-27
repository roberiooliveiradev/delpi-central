from __future__ import annotations

from unittest.mock import MagicMock

from tm_app.infrastructure.persistence.repositories.investimento_repository import (
    InvestimentoRepository,
)


def test_update_recalculates_valor_total():
    repo = InvestimentoRepository(connection=MagicMock())
    repo.execute_returning_one = MagicMock(
        return_value={
            "investimento_id": "i1",
            "quantidade": 3,
            "valor_unitario": 10,
            "valor_total": 30,
        }
    )

    row = repo.update(
        "i1",
        {
            "tipo_investimento": "unico",
            "descricao_item": "Licença",
            "quantidade": 3,
            "valor_unitario": 10,
            "recorrencia": "unico",
        },
    )

    assert row is not None
    assert row["valor_total"] == 30
    args = repo.execute_returning_one.call_args[0][1]
    assert args[5] == 30.0
