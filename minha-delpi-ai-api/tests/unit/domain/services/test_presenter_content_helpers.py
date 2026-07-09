from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def test_product_detail_title_from_presenter_content():
    presenter = ExternalActionResultPresenter()

    title = presenter._infer_items_title([], "/products/90260123/purchases")

    assert title == "Compras do produto"


def test_generic_kpi_cards_use_presenter_palette():
    presenter = ExternalActionResultPresenter()

    result = presenter.present(
        {
            "weighted_efficiency_pct": 98.5,
            "appointment_count": 120,
            "ignored": "x",
        },
        path="/production/eficiencia-fabril",
    )

    cards = (result.get("apresentacao") or {}).get("cards") or []

    assert len(cards) == 2
    assert cards[0]["unit"] == "%"
    assert cards[0]["color"] == "#0ea5e9"


def test_financial_rol_kpi_cards_use_portuguese_labels():
    presenter = ExternalActionResultPresenter()

    result = presenter.present(
        {
            "success": True,
            "data": {
                "gross_revenue": 5138916.92,
                "returns": 118597.25,
                "discounts": 12220.52,
                "icms": 191225.32,
                "rol": 5000000.0,
            },
            "meta": {
                "entity": "financial_rol",
                "shape": "scalar",
                "operationId": "get_financial_rol",
            },
        },
        path="/financial/rol",
    )

    joined = "\n".join(result.get("linhas") or [])

    assert "Receita bruta" in joined
    assert "Devoluções" in joined
    assert "R$" in joined
    assert "5.138.916,92" in joined
    assert "Gross revenue" not in joined
    assert "Returns" not in joined
    assert "branch: Filial" not in joined


def test_product_overview_narrative_uses_content():
    presenter = ExternalActionResultPresenter()

    result = presenter.present(
        {
            "code": "10080001",
            "description": "TERM. BANDEIRA",
            "type": "MP",
            "unit": "PC",
            "group_code": "1008",
            "active": "S",
            "standard_cost": 0.03,
        },
        path="/products/10080001",
    )

    lines = result.get("linhas") or []

    assert any("TERM. BANDEIRA" in line for line in lines)
    assert any("Custo padrão" in line for line in lines)


def test_product_guide_ops_preview_from_content():
    presenter = ExternalActionResultPresenter()

    result = presenter.present(
        {
            "items": [
                {
                    "product_code": "90260123",
                    "bom_level": 0,
                    "operation_code": "01",
                    "operation_description": "EMBALAR",
                    "work_center": "CT-19",
                }
            ],
            "meta": {"entity": "product_guide"},
        },
        path="/products/90260123/guide",
    )

    joined = "\n".join(result["linhas"])

    assert "EMBALAR" in joined
    assert "90260123" in joined


def test_format_structure_component_line_via_table():
    presenter = ExternalActionResultPresenter()

    table = presenter._build_items_table(
        [
            {
                "code": "50220013",
                "description": "CABO",
                "type": "MP",
                "quantity": 2.5,
            }
        ],
        title="Estrutura do produto",
        path="/products/90260123/structure",
    )

    row_text = " ".join(str(value) for value in (table.get("rows") or [{}])[0].values())

    assert "50220013" in row_text
    assert "CABO" in row_text


def test_present_product_factory_status_uses_content():
    presenter = ExternalActionResultPresenter()

    result = presenter.present(
        {
            "product": {"code": "90260123", "description": "CABO"},
            "factory_status": "Ativo",
            "structure": {"summary": {"total_exclusive_raw_materials": 3}},
        },
        path="/products/90260123/factory-status",
    )

    assert result is not None
    joined = "\n".join(result.get("linhas") or [])
    assert "90260123" in joined or "Ativo" in joined


def test_format_inspection_characteristic_line_via_table():
    presenter = ExternalActionResultPresenter()

    table = presenter._build_items_table(
        [
            {
                "inspection_type": "Dimensional",
                "sequence": 1,
                "characteristic": "Comprimento",
            }
        ],
        title="Inspeção",
        path="/products/90260123/inspection",
    )

    row_text = " ".join(str(value) for value in (table.get("rows") or [{}])[0].values())

    assert "Comprimento" in row_text
    assert "Dimensional" in row_text


def test_present_items_stock_detail_uses_product_operational_content():
    presenter = ExternalActionResultPresenter()

    result = presenter.present(
        {
            "items": [
                {
                    "branch": "01",
                    "warehouse": "01",
                    "current_quantity": 10,
                    "available_quantity": 8,
                    "committed_quantity": 2,
                    "physical_location": "A-1",
                }
            ]
        },
        path="/products/90260123/stock",
    )

    assert result["titulo"] == "Estoque do produto"
    assert "Filial 01" in result["linhas"][0] or "Filial: 01" in result["linhas"][0]
    assert "A-1" in result["linhas"][0]


def test_path_fragment_title_reads_presenter_content():
    presenter = ExternalActionResultPresenter()

    assert presenter._infer_items_title([], "/products/90260123/stock") == "Estoque do produto"
    assert (
        presenter._infer_items_title([], "/products/90260123/structure")
        == "Estrutura do produto"
    )


def test_present_dict_fallback_uses_content():
    presenter = ExternalActionResultPresenter()

    result = presenter._present_dict_fallback(
        {"total": 3, "items": [{"code": "1"}]},
        "/custom/endpoint",
    )

    assert result is not None
    assert any("total" in line.lower() or "Total" in line for line in result["linhas"])


def test_route_presentation_keys_exist_for_mp_purchase_profiles():
    presenter = ExternalActionResultPresenter()

    assert "Preço de venda" in presenter._route_presentation(
        "salePricing",
        "titleWithCode",
        code="10080001",
    )
    assert presenter._route_presentation("lastPurchase", "kpiUnitPrice")
    assert presenter._route_presentation("purchasePriceHistory", "kpiLastVariation")
    assert presenter._route_presentation("purchaseBudgetHistory", "kpiPurchaseOrders")
    assert presenter._route_presentation("purchaseList", "ordersTableTitle")
