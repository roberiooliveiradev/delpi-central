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


def test_capabilities_catalog_uses_pt_labels():
    from app.application.services.chat_capabilities_service import ChatCapabilitiesService

    text = ChatCapabilitiesService.build_direct_answer(
        workspace_context={"agent": {"name": "Teste"}, "agentKey": "t"},
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
