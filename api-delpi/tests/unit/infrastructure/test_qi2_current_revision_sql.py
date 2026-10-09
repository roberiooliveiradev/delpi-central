"""GLPI #1219 — listagens/agregados QI2010 devem excluir revisões obsoletas.

Contrato: `QI2_OBSOL = 'S'` marca revisão obsoleta; `'N'` e legado em branco
são a revisão corrente de (QI2_FILIAL, QI2_FNC). Toda leitura operacional
deve aplicar `QI2_OBSOL <> 'S'` compartilhado via `QI2_CURRENT_REVISION_SQL`.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.application.dto.nonconformity.list_nonconformity_request import (
    ListNonconformityRequest,
)
from app.infrastructure.persistence.totvs.nonconformity_repositories.nonconformity_query_repository import (
    NonconformityQueryRepository,
)
from app.infrastructure.persistence.totvs.quality.qi2_record_sql import (
    QI2_CURRENT_REVISION_SQL,
)


def _opened_repo() -> NonconformityQueryRepository:
    repo = NonconformityQueryRepository()
    repo.connection = object()
    repo.cursor = object()
    repo._connect = lambda: None  # type: ignore[method-assign]
    repo._close = lambda *a, **k: None  # type: ignore[method-assign]
    return repo


def test_qi2_current_revision_sql_excludes_only_obsolete() -> None:
    assert QI2_CURRENT_REVISION_SQL == "QI2_OBSOL <> 'S'"


@patch.object(NonconformityQueryRepository, "execute_query", return_value=[])
@patch.object(NonconformityQueryRepository, "execute_scalar", return_value=0)
def test_list_nonconformities_filters_obsolete_in_count_and_page(
    mock_scalar: MagicMock,
    mock_query: MagicMock,
) -> None:
    repo = _opened_repo()
    repo.list_nonconformities(
        ListNonconformityRequest(type="all", branch="01", page=1, page_size=20)
    )

    count_sql = mock_scalar.call_args[0][0]
    page_sql = mock_query.call_args[0][0]

    assert "nc.QI2_OBSOL <> 'S'" in count_sql
    assert "nc.QI2_OBSOL <> 'S'" in page_sql
    # COUNT(1) e listagem compartilham o mesmo WHERE (mesmo recorte).
    count_where = count_sql.rsplit("WHERE", 1)[1]
    page_where = page_sql.rsplit("WHERE", 1)[1].split("ORDER BY", 1)[0]
    assert count_where.strip() == page_where.strip()


@patch.object(NonconformityQueryRepository, "execute_query", return_value=[])
@patch.object(NonconformityQueryRepository, "execute_scalar", return_value=0)
def test_list_nonconformities_keeps_logical_delete_and_pagination(
    mock_scalar: MagicMock,
    mock_query: MagicMock,
) -> None:
    repo = _opened_repo()
    repo.list_nonconformities(
        ListNonconformityRequest(type="all", branch="01", page=2, page_size=10)
    )

    page_sql, page_params = mock_query.call_args[0]
    assert "nc.D_E_L_E_T_ = ''" in page_sql
    assert "OFFSET ? ROWS" in page_sql
    assert list(page_params)[-2:] == [10, 10]  # offset=(page-1)*size


@patch.object(NonconformityQueryRepository, "execute_one", return_value={})
def test_sum_returned_quantity_filters_obsolete(
    mock_one: MagicMock,
) -> None:
    repo = _opened_repo()
    repo.sum_returned_quantity(ListNonconformityRequest(type="all", branch="01"))

    sql = mock_one.call_args[0][0]
    assert "QI2_OBSOL <> 'S'" in sql
    assert "D_E_L_E_T_ = ''" in sql
