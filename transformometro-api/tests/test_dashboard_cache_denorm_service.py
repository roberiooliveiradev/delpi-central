from __future__ import annotations

from tm_app.domain.services.dashboard_cache_denorm_service import (
    filial_filter_sql,
    is_uuid,
    resolve_cache_scope_for_review,
    setor_filter_sql,
)


def test_is_uuid():
    assert is_uuid("550e8400-e29b-41d4-a716-446655440000")
    assert not is_uuid("01")
    assert not is_uuid("engenharia")


def test_resolve_cache_scope_from_instancia():
    scope = resolve_cache_scope_for_review(
        {"instancia_id": "i1"},
        {"filial_id": "01", "setor_id": "eng"},
        instancias_by_id={
            "i1": {
                "instancia_id": "i1",
                "filial_id": "f-uuid",
                "setor_id": "s-uuid",
                "codigo_filial": "01",
                "codigo_setor": "engenharia",
            }
        },
    )
    assert scope["instancia_id"] == "i1"
    assert scope["filial_id"] == "f-uuid"
    assert scope["codigo_filial"] == "01"
    assert scope["codigo_setor"] == "engenharia"


def test_resolve_cache_scope_fallback_process_row():
    scope = resolve_cache_scope_for_review(
        {},
        {"filial_id": "02", "setor_id": "compras", "instancia_id": "i2"},
        instancias_by_id={},
    )
    assert scope["instancia_id"] == "i2"
    assert scope["filial_id"] is None
    assert scope["codigo_filial"] == "02"
    assert scope["codigo_setor"] == "compras"


def test_filial_filter_sql_codigo_vs_uuid():
    codigo_sql, codigo_params = filial_filter_sql("d", "01")
    uuid_sql, uuid_params = filial_filter_sql(
        "d", "550e8400-e29b-41d4-a716-446655440000"
    )
    assert "codigo_filial" in codigo_sql
    assert codigo_params == ("01",)
    assert "d.filial_id = %s::uuid" in uuid_sql
    assert uuid_params == ("550e8400-e29b-41d4-a716-446655440000",)


def test_setor_filter_sql_codigo_vs_uuid():
    codigo_sql, _ = setor_filter_sql("d", "engenharia")
    uuid_sql, _ = setor_filter_sql("d", "550e8400-e29b-41d4-a716-446655440000")
    assert "codigo_setor" in codigo_sql
    assert "d.setor_id = %s::uuid" in uuid_sql
