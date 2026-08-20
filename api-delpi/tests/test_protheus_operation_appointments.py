"""Testes — convenções canônicas do apontamento de operação (HZA010)."""

from __future__ import annotations

from app.domain.totvs import protheus_operation_appointments as hza
from app.domain.totvs import protheus_users


def test_physical_table_has_no_s_prefix() -> None:
    """A base Delpi tem HZA010; SHZA010 não existe e derruba a query."""
    assert hza.OPERATION_APPOINTMENT_TABLE == "HZA010"


def test_only_status_one_means_running() -> None:
    assert hza.APPOINTMENT_STATUS_RUNNING == "1"
    assert hza.APPOINTMENT_STATUS_CLOSED == "2"
    assert hza.APPOINTMENT_STATUS_DISCARDED == "3"


def test_active_predicate_requires_open_and_recent_appointment() -> None:
    predicate = hza.active_appointment_predicate_sql("Z")
    assert "Z.HZA_STATUS = '1'" in predicate
    assert "Z.HZA_DTFIM" in predicate
    assert "Z.HZA_DTINI >= ?" in predicate


def test_active_marker_segments_have_fixed_width() -> None:
    """Sem largura fixa o offset do operador quebra em campo vazio."""
    marker = hza.active_marker_sql("Z", operator_name_expr="NOME")
    for column, width in (
        ("HZA_DTINI", hza.ACTIVE_MARKER_DATE_LENGTH),
        ("HZA_HRINI", hza.ACTIVE_MARKER_TIME_LENGTH),
        ("HZA_OPERAD", hza.ACTIVE_MARKER_OPERATOR_LENGTH),
    ):
        assert f"Z.{column}" in marker
        assert f"', {width})" in marker
    assert marker.endswith("NOME")


def test_split_active_marker_reads_date_time_operator_and_name() -> None:
    marker = "2026081918:58:25000223SILVANA ANDRADE DOS SANTOS"
    assert hza.split_active_marker(marker) == (
        "20260819",
        "18:58:25",
        "000223",
        "SILVANA ANDRADE DOS SANTOS",
    )


def test_split_active_marker_tolerates_empty_marker() -> None:
    assert hza.split_active_marker("") == ("", "", "", "")
    assert hza.split_active_marker(None) == ("", "", "", "")


def test_operator_name_resolves_through_protheus_user_table() -> None:
    """HZA_OPERAD é usuário Protheus; SRA010 não cobre esses códigos."""
    assert protheus_users.PROTHEUS_USER_TABLE == "SYS_USR"
    join = protheus_users.operator_name_join_sql(alias="USR", operator_expr="X")
    assert "LEFT JOIN SYS_USR USR WITH (NOLOCK)" in join
    assert "USR.USR_ID" in join
