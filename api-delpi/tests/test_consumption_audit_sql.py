"""Consumption-audit SQL — read-only guarantees and parameter binding.

Every builder must produce a single ``SELECT`` statement: no writes, no DDL,
no dynamic values from the caller — only ``?`` placeholders bound by the
repository adapter. SD3 is fetched once per OP (never per component), and
D4_OPORIG stays visible so related OPs never double count.
"""

from __future__ import annotations

import re

import pytest

from app.infrastructure.persistence.totvs.production_repositories import (
    consumption_audit_sql,
)
from app.infrastructure.persistence.totvs.production_repositories.consumption_audit_repository import (
    ConsumptionAuditRepository,
)

_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|CREATE|TRUNCATE|EXEC|GRANT)\b",
    re.IGNORECASE,
)


def _assert_select_only(sql: str) -> None:
    normalized = re.sub(r"\s+", " ", sql).strip()
    assert normalized.upper().startswith("SELECT"), normalized[:80]
    assert not _FORBIDDEN.search(normalized), normalized
    assert ";" not in normalized, "múltiplas statements não são permitidas"


@pytest.mark.parametrize(
    "builder,args",
    [
        (consumption_audit_sql.order_sql, ()),
        (consumption_audit_sql.family_orders_sql, ()),
        (consumption_audit_sql.commitments_sql, ()),
        (consumption_audit_sql.movements_sql, ()),
        (consumption_audit_sql.appointments_sql, ()),
        (consumption_audit_sql.operation_events_sql, ()),
        (consumption_audit_sql.allocations_sql, ()),
        (consumption_audit_sql.routing_sql, ()),
        (consumption_audit_sql.bom_components_sql, ()),
        (consumption_audit_sql.product_metadata_sql, (3,)),
        (consumption_audit_sql.parent_consumers_sql, ()),
    ],
)
def test_all_queries_are_single_parameterized_selects(builder, args):
    sql = builder(*args)
    _assert_select_only(sql)


def test_movements_sql_is_one_op_level_query_not_per_component():
    sql = consumption_audit_sql.movements_sql()
    assert "D3_OP" in sql
    assert "D3_FILIAL" in sql
    # Uma única consulta por OP — sem placeholder de componente.
    assert sql.count("?") == 2


def test_commitments_sql_keeps_d4_oporig_visible_and_dedup_grain():
    sql = consumption_audit_sql.commitments_sql()
    assert "D4_OPORIG" in sql
    assert "GROUP BY" in sql
    assert "D4_OPERAC" in sql


def test_bom_uses_validity_filter_at_reference_date():
    sql = consumption_audit_sql.bom_components_sql()
    assert "G1_INI" in sql
    assert "G1_FIM" in sql
    # produto + filial + 2 placeholders do filtro de vigência.
    assert sql.count("?") == 4


def test_order_sql_uses_11_position_key_and_branch_filter():
    sql = consumption_audit_sql.order_sql()
    assert "C2_OP" in sql
    assert "C2_FILIAL" in sql
    assert sql.count("?") == 2


def test_product_metadata_sql_placeholder_count_matches_batch():
    sql = consumption_audit_sql.product_metadata_sql(5)
    assert sql.count("?") == 5
    with pytest.raises(ValueError):
        consumption_audit_sql.product_metadata_sql(0)


class _FakeRepo(ConsumptionAuditRepository):
    def __init__(self):
        self.queries: list[tuple[str, tuple]] = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute_one(self, query, params=()):
        self.queries.append((query, tuple(params)))
        return None

    def execute_query(self, query, params=()):
        self.queries.append((query, tuple(params)))
        return []


def test_repository_binds_parameters_in_placeholder_order():
    repo = _FakeRepo()

    repo.fetch_order(production_order="24884201006", branch="01")
    assert repo.queries[-1][1] == ("24884201006", "01")

    repo.fetch_movements(production_order="24884201006", branch="01")
    assert repo.queries[-1][1] == ("24884201006", "01")

    repo.fetch_commitments(production_order="24884201006", branch="02")
    assert repo.queries[-1][1] == ("24884201006", "02")

    repo.fetch_bom_components(
        product_code="50226108", branch="01", reference_date="20261020"
    )
    assert repo.queries[-1][1] == ("50226108", "01", "20261020", "20261020")

    repo.fetch_routing(product_code="50226108", branch="01")
    assert repo.queries[-1][1] == ("50226108", "01")

    repo.fetch_family_orders(
        order_number="248842", branch="01",
        exclude_production_order="24884201006",
    )
    assert repo.queries[-1][1] == ("01", "248842", "24884201006")

    repo.fetch_parent_consumers(production_order="24884201006", branch="01")
    assert repo.queries[-1][1] == ("24884201006", "01")

    repo.fetch_product_metadata(codes=["MOD216", "10010030", "MOD216", " "])
    assert repo.queries[-1][1] == ("10010030", "MOD216")
    assert repo.queries[-1][0].count("?") == 2


def test_repository_methods_only_execute_selects():
    repo = _FakeRepo()
    repo.fetch_order(production_order="24884201006", branch="01")
    repo.fetch_family_orders(
        order_number="248842", branch="01",
        exclude_production_order="24884201006",
    )
    repo.fetch_commitments(production_order="24884201006", branch="01")
    repo.fetch_movements(production_order="24884201006", branch="01")
    repo.fetch_appointments(production_order="24884201006", branch="01")
    repo.fetch_operation_events(production_order="24884201006", branch="01")
    repo.fetch_allocations(production_order="24884201006", branch="01")
    repo.fetch_routing(product_code="50226108", branch="01")
    repo.fetch_bom_components(
        product_code="50226108", branch="01", reference_date="20261020"
    )
    repo.fetch_product_metadata(codes=["10010030"])
    repo.fetch_parent_consumers(production_order="24884201006", branch="01")
    assert len(repo.queries) == 11
    for sql, _ in repo.queries:
        _assert_select_only(sql)
