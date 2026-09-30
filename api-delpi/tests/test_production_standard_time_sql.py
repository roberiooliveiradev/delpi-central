"""SQL — tempo padrão de operação única (SC2 + SHY010 + SG2010)."""

from app.infrastructure.persistence.totvs.production.production_standard_time_sql import (
    build_operation_standard_time_query,
)


def test_query_targets_sc2_shy_and_sg2() -> None:
    query = build_operation_standard_time_query()
    assert "FROM SC2010 OP" in query
    assert "FROM SHY010 SHY" in query
    assert "FROM SG2010 SG2" in query


def test_query_filters_deleted_rows_in_every_table() -> None:
    query = build_operation_standard_time_query()
    assert query.count("D_E_L_E_T_ = ''") == 3


def test_query_is_fully_parametrized() -> None:
    query = build_operation_standard_time_query()
    # SHY (filial, OP, operação) + SG2 (filial, operação) + SC2 (filial, OP)
    assert query.count("?") == 7
    assert "SHY.HY_FILIAL = ?" in query
    assert "SHY.HY_OP = ?" in query
    assert "SHY.HY_OPERAC = ?" in query
    assert "SG2.G2_FILIAL = ?" in query
    assert "SG2.G2_OPERAC = ?" in query
    assert "OP.C2_FILIAL = ?" in query
    assert "OP.C2_OP = ?" in query


def test_query_does_not_interpolate_user_input() -> None:
    query = build_operation_standard_time_query()
    for needle in ("{branch}", "{production_order}", "{operation_code}"):
        assert needle not in query


def test_sg2_scoped_to_the_order_routing() -> None:
    query = build_operation_standard_time_query()
    assert "SG2.G2_PRODUTO = OP.C2_PRODUTO" in query
    assert "SG2.G2_CODIGO = OP.C2_ROTEIRO" in query


def test_shy_and_sg2_pick_latest_record() -> None:
    query = build_operation_standard_time_query()
    assert query.count("SELECT TOP 1") == 2
    assert "ORDER BY SHY.R_E_C_N_O_ DESC" in query
    assert "ORDER BY SG2.R_E_C_N_O_ DESC" in query


def test_operation_exists_flag_covers_shy_or_sg2() -> None:
    query = build_operation_standard_time_query()
    assert "operation_exists" in query
    assert "SHY.has_row = 1 OR SG2.has_row = 1" in query


def test_query_never_depends_on_efficiency_view() -> None:
    query = build_operation_standard_time_query()
    assert "vw_Apontamentos_Eficiencia" not in query
    assert "SH6010" not in query
    assert "HZA010" not in query
