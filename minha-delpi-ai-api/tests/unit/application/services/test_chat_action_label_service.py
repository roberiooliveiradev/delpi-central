from app.application.services.chat_action_label_service import ChatActionLabelService
from app.domain.services.action_display_label_resolver import (
    SOURCE_ENGLISH_SUMMARY_MAP,
    SOURCE_OPENAPI_LOCALIZED,
    SOURCE_OPENAPI_SUMMARY,
    ActionDisplayLabelResolver,
)


def test_humanize_commercial_closing_rate_uses_locale_not_path_label(monkeypatch):
    monkeypatch.setenv("ACTION_DISPLAY_LABEL_MODE", "default")
    result = ActionDisplayLabelResolver.resolve(
        path="/commercial/closing-rate",
        method="GET",
        summary="Get Sales Conversion Rate",
        delpi_metadata={
            "locale": {"pt-BR": {"summary": "Taxa de conversão de vendas"}},
        },
    )
    assert result.label == "Taxa de conversão de vendas"
    assert result.source == SOURCE_OPENAPI_LOCALIZED


def test_humanize_product_customers_english_map_bridge(monkeypatch):
    monkeypatch.setenv("ACTION_DISPLAY_LABEL_MODE", "default")
    result = ActionDisplayLabelResolver.resolve(
        path="/products/{code}/customers",
        method="GET",
        summary="Customers",
    )
    assert result.label == "Clientes do produto"
    assert result.source == SOURCE_ENGLISH_SUMMARY_MAP


def test_humanize_keeps_portuguese_summary(monkeypatch):
    monkeypatch.setenv("ACTION_DISPLAY_LABEL_MODE", "default")
    result = ActionDisplayLabelResolver.resolve(
        path="/products/{code}/stock",
        method="GET",
        summary="Estoque do produto por filial e local",
    )
    assert "Estoque" in result.label
    assert result.source == SOURCE_OPENAPI_SUMMARY


def test_humanize_hr_snapshot(monkeypatch):
    monkeypatch.setenv("ACTION_DISPLAY_LABEL_MODE", "default")
    label = ChatActionLabelService.humanize(
        path="/hr/snapshot",
        method="GET",
        summary="Get Hr Snapshot",
    )
    assert label == "Snapshot de indicadores de RH"


def test_humanize_commercial_proposals_english_map(monkeypatch):
    monkeypatch.setenv("ACTION_DISPLAY_LABEL_MODE", "default")
    label = ChatActionLabelService.humanize(
        path="/commercial/proposals",
        method="GET",
        summary="Commercial proposals listed successfully.",
    )
    assert label == "Propostas comerciais listadas"


def test_humanize_production_oee_series(monkeypatch):
    monkeypatch.setenv("ACTION_DISPLAY_LABEL_MODE", "default")
    label = ChatActionLabelService.humanize(
        path="/production/oee/series",
        method="GET",
        summary="OEE series",
    )
    assert label == "Série histórica de OEE"


def test_humanize_production_oee_detail(monkeypatch):
    monkeypatch.setenv("ACTION_DISPLAY_LABEL_MODE", "default")
    label = ChatActionLabelService.humanize(
        path="/production/oee",
        method="GET",
        summary="Get production oee",
    )
    assert "OEE produção" in label


def test_humanize_production_oee_appointment(monkeypatch):
    monkeypatch.setenv("ACTION_DISPLAY_LABEL_MODE", "default")
    label = ChatActionLabelService.humanize(
        path="/production/oee/appointments/12345",
        method="GET",
        summary="Get production oee appointment by id",
    )
    assert "apontamento OEE" in label


def test_humanize_system_table_schema(monkeypatch):
    monkeypatch.setenv("ACTION_DISPLAY_LABEL_MODE", "default")
    label = ChatActionLabelService.humanize(
        path="/system/tables/SB1/schema",
        method="GET",
        summary="Table schema",
    )
    assert label == "Schema completo da tabela"


def test_humanize_eficiencia_fabril_dashboard(monkeypatch):
    monkeypatch.setenv("ACTION_DISPLAY_LABEL_MODE", "default")
    label = ChatActionLabelService.humanize(
        path="/production/eficiencia-fabril/dashboard",
        method="GET",
        summary="Eficiencia fabril dashboard",
    )
    assert label == "Painel de eficiência fabril"


def test_default_mode_ignores_path_labels_when_locale_present(monkeypatch):
    monkeypatch.setenv("ACTION_DISPLAY_LABEL_MODE", "default")
    result = ActionDisplayLabelResolver.resolve(
        path="/products/{code}/stock",
        method="GET",
        summary="Get product stock",
        delpi_metadata={
            "locale": {"pt-BR": {"summary": "Consultar estoque do produto por filial"}},
        },
    )
    assert result.source == SOURCE_OPENAPI_LOCALIZED
    assert result.label == "Consultar estoque do produto por filial"


def test_capabilities_catalog_uses_locale_and_english_map(monkeypatch):
    monkeypatch.setenv("ACTION_DISPLAY_LABEL_MODE", "default")
    from app.application.services.chat_capabilities_service import ChatCapabilitiesService

    text = ChatCapabilitiesService.build_direct_answer(
        workspace_context={
            "agent": {"name": "Teste"},
            "agentId": "11111111-1111-4111-8111-111111111111",
        },
        allowed_action_ids=["a1", "a2"],
        action_catalog=[
            {
                "actionId": "a1",
                "method": "GET",
                "path": "/commercial/closing-rate",
                "summary": "Get Sales Conversion Rate",
                "delpiMetadata": {
                    "locale": {"pt-BR": {"summary": "Taxa de conversão de vendas"}},
                },
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
