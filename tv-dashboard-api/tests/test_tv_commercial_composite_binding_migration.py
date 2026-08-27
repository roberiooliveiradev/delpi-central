"""Migração de bindings das compostas ROL/OTD para rotas simples."""

from __future__ import annotations

from tv_app.application.services.data.tv_commercial_composite_binding_migration_service import (
    migrate_composite_commercial_binding,
    resolve_simple_commercial_operation_id,
)
from tv_app.application.services.data.tv_data_binding_hydrate_service import (
    hydrate_comunicado_data_bindings,
)


def test_resolve_rol_by_display_mode_and_group_by():
    assert (
        resolve_simple_commercial_operation_id(
            "get_commercial_rol", display_mode="kpi", params={}
        )
        == "get_si_indicator_commercial_rol_realized"
    )
    assert (
        resolve_simple_commercial_operation_id(
            "get_commercial_rol", display_mode="line_chart", params={}
        )
        == "get_commercial_rol_series"
    )
    assert (
        resolve_simple_commercial_operation_id(
            "get_commercial_rol",
            display_mode="table",
            params={"group_by": "customer"},
        )
        == "get_commercial_rol_by_customer"
    )
    assert (
        resolve_simple_commercial_operation_id(
            "get_commercial_rol",
            display_mode="table",
            params={"group_by": "branch"},
        )
        == "get_commercial_rol_by_branch"
    )


def test_resolve_otd_by_display_mode_and_group_by():
    assert (
        resolve_simple_commercial_operation_id(
            "get_commercial_sales_order_otd_analysis",
            display_mode="kpi",
            params={},
        )
        == "get_sales_order_otd"
    )
    assert (
        resolve_simple_commercial_operation_id(
            "get_commercial_sales_order_otd_analysis",
            display_mode="line_chart",
            params={},
        )
        == "get_sales_order_otd_series"
    )
    assert (
        resolve_simple_commercial_operation_id(
            "get_commercial_sales_order_otd_analysis",
            display_mode="table",
            params={"group_by": "branch"},
        )
        == "get_sales_order_otd_by_branch"
    )


def test_migrate_binding_strips_group_by_and_remaps_fields():
    migrated = migrate_composite_commercial_binding(
        {
            "operationId": "get_commercial_rol",
            "displayMode": "line_chart",
            "params": {"group_by": "none", "granularity": "month", "branch": "01"},
            "transformSteps": [
                {"op": "select", "columns": ["period_label", "rol_filial_01", "rol_filial_02"]}
            ],
        }
    )
    assert migrated["operationId"] == "get_commercial_rol_series"
    assert "group_by" not in migrated["params"]
    assert migrated["params"]["granularity"] == "month"
    assert migrated["transformSteps"][0]["columns"] == [
        "periodo",
        "rol_matrix",
        "rol_branch",
    ]


class _FakeCatalog:
    def __init__(self, routes: dict) -> None:
        self._routes = routes

    def get_route(self, operation_id: str):
        return self._routes.get(operation_id)


def test_hydrate_migrates_composite_before_catalog_lookup():
    catalog = _FakeCatalog(
        {
            "get_commercial_rol_by_customer": {
                "label": "ROL por cliente",
                "paramSchema": {
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "branch": {"type": "string", "optional": True},
                },
            }
        }
    )
    cfg, summary = hydrate_comunicado_data_bindings(
        {
            "blocks": [
                {
                    "id": "a",
                    "type": "data_source",
                    "dataBinding": {
                        "operationId": "get_commercial_rol",
                        "displayMode": "table",
                        "params": {
                            "group_by": "customer",
                            "start_date": "2026-06-01",
                            "end_date": "2026-06-30",
                            "granularity": "week",
                        },
                    },
                }
            ]
        },
        catalog=catalog,
    )
    binding = cfg["blocks"][0]["dataBinding"]
    assert binding["operationId"] == "get_commercial_rol_by_customer"
    assert "group_by" not in binding["params"]
    assert "granularity" not in binding["params"]
    assert summary["orphanOperationIds"] == []
