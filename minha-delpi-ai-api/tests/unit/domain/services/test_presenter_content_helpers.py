from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def test_product_detail_title_from_presenter_content():
    presenter = ExternalActionResultPresenter()

    title = presenter._product_detail_title(
        "90260123",
        {"purchases": [{"qty": 1}]},
    )

    assert title == "Compras do produto 90260123"


def test_generic_kpi_cards_use_presenter_palette():
    presenter = ExternalActionResultPresenter()

    cards = presenter._build_generic_kpi_cards(
        {
            "weighted_efficiency_pct": 98.5,
            "appointment_count": 120,
            "ignored": "x",
        },
        path="/production/eficiencia-fabril",
    )

    assert cards is not None
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

    lines = presenter._build_product_overview_narrative_lines(
        {
            "code": "10080001",
            "description": "TERM. BANDEIRA",
            "type": "MP",
            "unit": "PC",
            "group_code": "1008",
            "active": "S",
            "standard_cost": 0.03,
        },
        {},
    )

    assert any("TERM. BANDEIRA" in line for line in lines)
    assert any("Custo padrão vigente" in line for line in lines)


def test_product_guide_ops_preview_from_content():
    presenter = ExternalActionResultPresenter()

    result = presenter._present_product_guide(
        [
            {
                "product_code": "90260123",
                "bom_level": 0,
                "operation_code": "01",
                "operation_description": "EMBALAR",
                "work_center": "CT-19",
            }
        ],
        path="/products/90260123/guide",
    )

    joined = "\n".join(result["linhas"])

    assert "**01** EMBALAR" in joined
    assert "90260123" in joined


def test_format_structure_component_line():
    presenter = ExternalActionResultPresenter()

    line = presenter._format_structure_component_line(
        "50220013",
        "CABO",
        "MP",
        2.5,
    )

    assert "50220013" in line
    assert "CABO" in line
    assert "MP" in line
    assert "2,5" in line or "2.5" in line


def test_format_inspection_characteristic_line():
    presenter = ExternalActionResultPresenter()

    line = presenter._format_inspection_characteristic_line(
        {
            "inspection_type": "Dimensional",
            "sequence": 1,
            "characteristic": "Comprimento",
        }
    )

    assert "Comprimento" in line
    assert "Dimensional" in line
    assert "seq." in line


def test_present_items_stock_detail_uses_product_operational_content():
    presenter = ExternalActionResultPresenter()

    result = presenter._present_items(
        [
            {
                "branch": "01",
                "warehouse": "01",
                "current_quantity": 10,
                "available_quantity": 8,
                "committed_quantity": 2,
                "physical_location": "A-1",
            }
        ],
    )

    assert result["titulo"] == "Estoque do produto"
    assert "Filial 01" in result["linhas"][0]
    assert "A-1" in result["linhas"][0]


def test_path_fragment_title_reads_presenter_content():
    presenter = ExternalActionResultPresenter()

    assert presenter._path_fragment_title("/stock") == "Estoque do produto"
    assert presenter._path_fragment_title("structure") == "Estrutura do produto"


def test_present_dict_fallback_uses_content():
    presenter = ExternalActionResultPresenter()

    result = presenter._present_dict_fallback(
        {"total": 3, "items": [{"code": "1"}]},
        "/custom/endpoint",
    )

    assert result is not None
    assert any("total" in line.lower() or "Total" in line for line in result["linhas"])
