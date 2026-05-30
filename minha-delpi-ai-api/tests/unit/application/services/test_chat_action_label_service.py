from app.application.services.chat_action_label_service import ChatActionLabelService


def test_humanize_commercial_closing_rate():
    label = ChatActionLabelService.humanize(
        path="/commercial/closing-rate",
        method="GET",
        summary="Get Sales Conversion Rate",
    )
    assert label == "Taxa de conversão de vendas"


def test_humanize_product_customers():
    label = ChatActionLabelService.humanize(
        path="/products/{code}/customers",
        method="GET",
        summary="Customers",
    )
    assert label == "Clientes do produto"


def test_humanize_keeps_portuguese_summary():
    label = ChatActionLabelService.humanize(
        path="/products/{code}/stock",
        method="GET",
        summary="Estoque do produto por filial e local",
    )
    assert "Estoque" in label


def test_humanize_hr_snapshot():
    label = ChatActionLabelService.humanize(
        path="/hr/snapshot",
        method="GET",
        summary="Get Hr Snapshot",
    )
    assert label == "Snapshot de indicadores de RH"


def test_humanize_commercial_proposals():
    label = ChatActionLabelService.humanize(
        path="/commercial/proposals",
        method="GET",
        summary="Commercial proposals listed successfully.",
    )
    assert label == "Propostas comerciais (ganhas, abertas ou todas)"


def test_humanize_production_oee_series():
    label = ChatActionLabelService.humanize(
        path="/production/oee/series",
        method="GET",
        summary="OEE series",
    )
    assert label == "Série histórica de OEE (produção)"


def test_humanize_system_table_schema():
    label = ChatActionLabelService.humanize(
        path="/system/tables/SB1/schema",
        method="GET",
        summary="Table schema",
    )
    assert label == "Schema completo da tabela (SX2/SX3/SIX/SX9)"


def test_humanize_eficiencia_fabril_dashboard():
    label = ChatActionLabelService.humanize(
        path="/production/eficiencia-fabril/dashboard",
        method="GET",
        summary="Eficiencia fabril dashboard",
    )
    assert label == "Painel de eficiência fabril (apontamentos)"


def test_capabilities_catalog_uses_pt_labels():
    from app.application.services.chat_capabilities_service import ChatCapabilitiesService

    text = ChatCapabilitiesService.build_direct_answer(
        workspace_context={"agent": {"name": "Teste"}, "agentId": "11111111-1111-4111-8111-111111111111"},
        allowed_action_ids=["a1", "a2"],
        action_catalog=[
            {
                "actionId": "a1",
                "method": "GET",
                "path": "/commercial/closing-rate",
                "summary": "Get Sales Conversion Rate",
            },
            {
                "actionId": "a2",
                "method": "GET",
                "path": "/products/{code}/suppliers",
                "summary": "Suppliers",
            },
        ],
    )
    assert "Taxa de conversão de vendas" in text
    assert "Fornecedores do produto" in text
    assert "Get Sales Conversion Rate" not in text
    assert "Suppliers —" not in text
