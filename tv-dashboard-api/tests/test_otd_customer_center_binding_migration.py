"""Slide migration: `cliente_loja_centro` → `customer_center` (OTD por cliente).

O campo sintético era produzido por transform (addColumn) a partir de
nome/loja/filtro; a API agora emite `customer_center` (SA7010.A7_XCENT) nas
rotas por cliente. A migração remove o produtor sintético e reponta refs.
"""

from __future__ import annotations

from tv_app.application.services.data.otd_customer_center_binding_migration import (
    CANONICAL_FIELD,
    LEGACY_FIELD,
    collect_customer_center_refs,
    migrate_native_config,
)


def _slide_config() -> dict:
    return {
        "blocks": [
            {
                "id": "src-1",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "get_sales_order_otd_series_by_customer",
                    "params": {
                        "customer_code_stores": "000001|06",
                        "customer_centers": "1700",
                    },
                    "transformSteps": [
                        {
                            "op": "addColumn",
                            "name": LEGACY_FIELD,
                            "expr": "customer_name & ' · Loja ' & customer_store",
                        },
                        {"op": "select", "columns": ["customer_name", LEGACY_FIELD]},
                    ],
                },
            },
            {
                "id": "tbl-1",
                "type": "data_table",
                "dataSourceId": "src-1",
                "title": "Cliente + Loja + Centro",
                "config": {
                    "selectedValueFields": ["customer_name", LEGACY_FIELD],
                    "cells": [{"dataRef": "items.cliente_loja_centro"}],
                },
            },
            {
                "id": "tbl-other",
                "type": "data_table",
                "dataBinding": {"operationId": "get_sales_order_otd_by_branch"},
                "config": {
                    "selectedValueFields": [LEGACY_FIELD],
                },
            },
        ]
    }


def test_migrates_producer_step_and_consumer_refs():
    migrated, applied = migrate_native_config(_slide_config())

    assert applied
    source = migrated["blocks"][0]
    steps = source["dataBinding"]["transformSteps"]
    assert [step["name"] for step in steps if step["op"] == "addColumn"] == []
    select = next(step for step in steps if step["op"] == "select")
    assert select["columns"] == ["customer_name", CANONICAL_FIELD]

    table = migrated["blocks"][1]
    assert table["config"]["selectedValueFields"] == [
        "customer_name",
        CANONICAL_FIELD,
    ]
    assert table["config"]["cells"][0]["dataRef"] == "items.customer_center"
    # Texto de exibição não é ref — permanece como caption do operador.
    assert table["title"] == "Cliente + Loja + Centro"


def test_does_not_touch_blocks_of_other_routes():
    migrated, _ = migrate_native_config(_slide_config())
    other = migrated["blocks"][2]
    assert other["config"]["selectedValueFields"] == [LEGACY_FIELD]


def test_request_params_are_not_response_data():
    migrated, _ = migrate_native_config(_slide_config())
    params = migrated["blocks"][0]["dataBinding"]["params"]
    assert params == {
        "customer_code_stores": "000001|06",
        "customer_centers": "1700",
    }


def test_idempotent_rerun_returns_no_refs():
    migrated, _ = migrate_native_config(_slide_config())
    again, refs = migrate_native_config(migrated)
    assert refs == []
    assert again == migrated


def test_collect_reports_producer_and_refs():
    refs = collect_customer_center_refs(_slide_config())
    kinds = {ref["kind"] for ref in refs}
    assert "producer_step" in kinds
    assert "field_ref" in kinds
    assert all(ref["operationId"] == "get_sales_order_otd_series_by_customer" for ref in refs)


def test_rename_step_producing_legacy_field_is_dropped():
    config = {
        "blocks": [
            {
                "id": "src",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "get_sales_order_otd_by_customer",
                    "transformSteps": [
                        {"op": "rename", "from": "centro", "to": LEGACY_FIELD},
                    ],
                },
            }
        ]
    }
    migrated, applied = migrate_native_config(config)
    assert migrated["blocks"][0]["dataBinding"]["transformSteps"] == []
    assert any(ref["kind"] == "producer_step" for ref in applied)


def test_unbound_legacy_refs_are_untouched():
    config = {
        "blocks": [
            {
                "id": "free",
                "type": "data_table",
                "config": {"selectedValueFields": [LEGACY_FIELD]},
            }
        ]
    }
    migrated, applied = migrate_native_config(config)
    assert applied == []
    assert migrated == config
