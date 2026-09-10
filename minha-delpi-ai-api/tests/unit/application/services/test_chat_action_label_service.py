from app.application.services.chat_action_label_service import ChatActionLabelService
from app.domain.services.action_display_label_resolver import (
    SOURCE_DETERMINISTIC_HUMANIZE,
    SOURCE_OPENAPI_LOCALIZED,
    SOURCE_OPENAPI_SUMMARY,
    ActionDisplayLabelResolver,
)


def test_humanize_commercial_closing_rate_uses_locale_not_path_label(monkeypatch):
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


def test_humanize_product_customers_deterministic(monkeypatch):
    result = ActionDisplayLabelResolver.resolve(
        path="/products/{code}/customers",
        method="GET",
        summary="Customers",
    )
    assert "cliente" in result.label.casefold()
    assert result.source == SOURCE_DETERMINISTIC_HUMANIZE


def test_humanize_keeps_portuguese_summary(monkeypatch):
    result = ActionDisplayLabelResolver.resolve(
        path="/products/{code}/stock",
        method="GET",
        summary="Estoque do produto por filial e local",
    )
    assert "Estoque" in result.label
    assert result.source == SOURCE_OPENAPI_SUMMARY


def test_humanize_hr_snapshot(monkeypatch):
    label = ChatActionLabelService.humanize(
        path="/hr/snapshot",
        method="GET",
        summary="Get Hr Snapshot",
    )
    assert "snapshot" in label.casefold() or "rh" in label.casefold()


def test_humanize_production_oee_series(monkeypatch):
    label = ChatActionLabelService.humanize(
        path="/production/oee/series",
        method="GET",
        summary="OEE series",
    )
    assert "série" in label.casefold() or "oee" in label.casefold()


def test_humanize_system_table_schema(monkeypatch):
    label = ChatActionLabelService.humanize(
        path="/system/tables/SB1/schema",
        method="GET",
        summary="Table schema",
    )
    assert "schema" in label.casefold() or "tabela" in label.casefold()


def test_humanize_eficiencia_fabril_dashboard(monkeypatch):
    label = ChatActionLabelService.humanize(
        path="/production/eficiencia-fabril/dashboard",
        method="GET",
        summary="Eficiencia fabril dashboard",
    )
    assert "painel" in label.casefold() or "efici" in label.casefold()


def test_locale_wins_over_english_summary(monkeypatch):
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


def test_capabilities_catalog_uses_locale(monkeypatch):
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
                "delpiMetadata": {
                    "locale": {"pt-BR": {"summary": "Fornecedores do produto"}},
                },
            },
        ],
    )
    assert "Taxa de conversão de vendas" in text
    assert "Fornecedores do produto" in text
    assert "Get Sales Conversion Rate" not in text
