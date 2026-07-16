from app.infrastructure.persistence.totvs.production_appointments.production_appointments_sql import (
    build_appointments_list_query,
    build_appointments_where,
    build_by_op_query,
    build_series_query,
    build_summary_by_ct_query,
    build_work_centers_catalog_query,
)


def test_appointments_where_closed_open_and_filters() -> None:
    where, params = build_appointments_where(
        date_start="20260615",
        date_end_exclusive="20260716",
        branch="01",
        work_center="CT-70",
        op="24620601001",
        product="90264227",
    )

    assert "SH6.D_E_L_E_T_ = ' '" in where
    assert "SH6.H6_TIPO = 'P'" in where
    assert "SH6.H6_DTAPONT >= ?" in where
    assert "SH6.H6_DTAPONT < ?" in where
    assert "LTRIM(RTRIM(SH1.H1_CTRAB)) = ?" in where
    assert params == [
        "01",
        "20260615",
        "20260716",
        "CT-70",
        "24620601001",
        "90264227",
    ]


def test_work_centers_catalog_marks_final_inspection() -> None:
    query, params = build_work_centers_catalog_query(branch="01")
    assert "SHB010 HB WITH (NOLOCK)" in query
    assert "%INSPE%FINAL%" in query
    assert "is_final_inspection" in query
    assert params == ("01",)


def test_summary_by_ct_converts_mi_with_display_factor() -> None:
    query, params = build_summary_by_ct_query(
        date_start="20260615",
        date_end_exclusive="20260716",
        branch="01",
    )
    assert "SH6010 SH6 WITH (NOLOCK)" in query
    assert "SH1010 SH1 WITH (NOLOCK)" in query
    assert "SHB010 HB WITH (NOLOCK)" in query
    assert "GROUP BY SH1.H1_CTRAB, HB.HB_NOME" in query
    assert "IN ('', 'MI')" in query
    assert "THEN 1000" in query
    assert params[0] == "01"


def test_by_op_exposes_unit_for_normalize() -> None:
    query, _params = build_by_op_query(
        date_start="20260615",
        date_end_exclusive="20260716",
        branch="01",
        offset=0,
        page_size=25,
    )
    assert "MAX(LTRIM(RTRIM(SB1.B1_UM))) AS unit" in query
    assert "OFFSET 0 ROWS FETCH NEXT 25 ROWS ONLY" in query


def test_series_day_work_center_groups_both() -> None:
    query, _params = build_series_query(
        date_start="20260615",
        date_end_exclusive="20260716",
        branch="02",
        group_by="day_work_center",
    )
    assert "GROUP BY SH6.H6_DTAPONT, SH1.H1_CTRAB, HB.HB_NOME" in query
    assert "work_center" in query
    assert "THEN 1000" in query


def test_by_op_uses_offset_fetch() -> None:
    query, _params = build_by_op_query(
        date_start="20260615",
        date_end_exclusive="20260716",
        branch="01",
        offset=50,
        page_size=25,
    )
    assert "OFFSET 50 ROWS FETCH NEXT 25 ROWS ONLY" in query
    assert "production_order" in query


def test_appointments_list_exposes_datetime_operator_and_resource() -> None:
    query, _params = build_appointments_list_query(
        date_start="20260615",
        date_end_exclusive="20260716",
        branch="01",
        offset=0,
        page_size=20,
    )
    assert "H6_HORAINI" in query
    assert "H6_HORAFIN" in query
    assert "H6_OPERADO" in query
    assert "SYS_USR" in query
    assert "AS operator_name" in query
    assert "AS resource_name" in query
    assert "AS start_time" in query
    assert "AS end_time" in query
    assert "ORDER BY SH6.H6_DTAPONT DESC, SH6.H6_HORAINI DESC" in query
