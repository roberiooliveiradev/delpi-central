from app.domain.services.chat_presentation_column_label_context import (
    ExternalActionColumnLabelContext,
)
from app.domain.services.chat_presentation_operational_table_service import (
    ChatPresentationOperationalTableService as OpsTable,
)
from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
    invalidate_column_label_cache,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from app.domain.services.external_actions.presenters.product_operational_table_row_enrichment import (
    normalize_lmp_items,
)


def test_resolve_columns_includes_all_api_fields_with_hint_order():
    invalidate_column_label_cache()
    service = ExternalActionColumnLabelService()
    items = [
        {
            "rank": 1,
            "raw_material_code": "10010032",
            "quantity_per_pa": 290,
            "unit": "MT",
            "extended_cost": 27.77,
            "impact_on_material_cost_percent": 0.05,
            "simulated_unit_cost": 0.09,
        }
    ]

    columns = service.resolve_columns_for_items(
        items,
        path="/products/90261255/cost-impact-simulation",
        profile_name="costImpactMaterials",
    )
    keys = [column["key"] for column in columns]

    assert "unit" in keys
    assert "simulated_unit_cost" in keys
    assert keys.index("rank") < keys.index("unit") < keys.index("simulated_unit_cost")


def test_build_items_table_surfaces_new_fields_without_fixed_whitelist():
    invalidate_column_label_cache()
    presenter = ExternalActionResultPresenter()
    table = OpsTable.build_items_table(
        presenter.column_label_context,
        [
            {
                "rank": 1,
                "raw_material_code": "10010032",
                "unit": "MT",
                "future_api_field": "novo",
            }
        ],
        path="/products/90261255/cost-impact-simulation",
        profile_name="costImpactMaterials",
        title="Ranking",
        role="list",
    )

    assert table is not None
    keys = [column["key"] for column in table["columns"]]

    assert "future_api_field" in keys
    assert table["rows"][0]["future_api_field"] == "novo"


def test_build_items_table_lmp_includes_new_api_fields():
    invalidate_column_label_cache()
    presenter = ExternalActionResultPresenter()
    table = OpsTable.build_items_table(
        presenter.column_label_context,
        normalize_lmp_items(
            [
                {
                    "saleNumber": "OV123",
                    "branch": "01",
                    "listingKind": "LMP",
                    "engineering_status": "A",
                    "saleDescription": "Pedido teste",
                    "new_lmp_field": "valor",
                }
            ]
        ),
        profile_name="lmpList",
        title="LMPs",
        role="lmp",
        path="/lmp",
    )

    assert table is not None
    keys = [column["key"] for column in table["columns"]]

    assert "sale_number" in keys
    assert "new_lmp_field" in keys
    assert table["rows"][0]["sale_number"] == "OV123"


def test_build_items_table_accepts_column_label_context_without_presenter():
    invalidate_column_label_cache()
    context = ExternalActionColumnLabelContext(
        column_labels=ExternalActionColumnLabelService(),
    )
    table = OpsTable.build_items_table(
        context,
        [{"alpha_field": 1, "beta_field": 2}],
        title="Fake",
        role="list",
        path="/fake",
    )

    assert table is not None
    keys = [column["key"] for column in table["columns"]]

    assert "alpha_field" in keys
    assert "beta_field" in keys


def test_build_profile_items_table_delegates_to_operational_builder():
    invalidate_column_label_cache()
    presenter = ExternalActionResultPresenter()
    table = presenter._build_profile_items_table(
        [{"order_number": "PC1", "branch": "01", "extra_field": "x"}],
        profile_name="purchaseOrderList",
        title="Pedidos",
        role="list",
        path="/purchases",
    )

    assert table is not None
    keys = [column["key"] for column in table["columns"]]

    assert "order_number" in keys
    assert "extra_field" in keys
