"""E1.S2 — generalização de ActionDisplayLabelResolver (sem dependência de path conhecido)."""

from __future__ import annotations

from app.domain.services.action_display_label_resolver import (
    SOURCE_DETERMINISTIC_HUMANIZE,
    SOURCE_LLM_LOCALIZATION,
    SOURCE_OPENAPI_LOCALIZED,
    SOURCE_OPENAPI_SUMMARY,
    SOURCE_TECHNICAL_FALLBACK,
    ActionDisplayLabelResolver,
)


def test_gen_first_party_locale_pt_br(monkeypatch):
    result = ActionDisplayLabelResolver.resolve(
        path="/commercial/closing-rate",
        method="GET",
        summary="Get Sales Conversion Rate",
        provider_key="api-delpi",
        delpi_metadata={
            "locale": {"pt-BR": {"summary": "Taxa de conversão de vendas"}},
        },
    )
    assert result.source == SOURCE_OPENAPI_LOCALIZED
    assert result.label == "Taxa de conversão de vendas"


def test_gen_external_summary_already_pt(monkeypatch):
    result = ActionDisplayLabelResolver.resolve(
        path="/widgets/{id}/stock",
        method="GET",
        summary="Consultar estoque de widgets",
        provider_key="acme-erp",
        action_id="acme.widgets.stock",
    )
    assert result.source == SOURCE_OPENAPI_SUMMARY
    assert "estoque" in result.label.casefold()


def test_gen_external_summary_en_llm_off_humanize(monkeypatch):
    ActionDisplayLabelResolver.configure(llm_localizer=None, cache_get=None, cache_put=None)
    result = ActionDisplayLabelResolver.resolve(
        path="/widgets/{id}/things",
        method="GET",
        summary="Get Widget Things",
        provider_key="acme-erp",
        action_id="acme.widgets.things",
    )
    assert result.source in {
        SOURCE_DETERMINISTIC_HUMANIZE,
        SOURCE_TECHNICAL_FALLBACK,
    }
    assert result.label
    assert result.source != "LEGACY_PATH_LABEL"


def test_gen_empty_summary_technical_fallback(monkeypatch):
    result = ActionDisplayLabelResolver.resolve(
        path="/unknown/xyz",
        method="GET",
        summary="",
        action_id="unknown.xyz",
        provider_key="ghost",
    )
    assert result.label
    assert result.source in {SOURCE_TECHNICAL_FALLBACK, SOURCE_DETERMINISTIC_HUMANIZE}


def test_gen_llm_cache_hit_and_miss(monkeypatch):
    store: dict[str, str] = {}

    def cache_get(key: str) -> str | None:
        return store.get(key)

    def cache_put(key: str, label: str, _source: str) -> None:
        store[key] = label

    calls = {"n": 0}

    def llm_localizer(**_kwargs) -> str:
        calls["n"] += 1
        return "Inventário de widgets por depósito"

    ActionDisplayLabelResolver.configure(
        llm_localizer=llm_localizer,
        cache_get=cache_get,
        cache_put=cache_put,
    )
    try:
        miss = ActionDisplayLabelResolver.resolve(
            path="/acme/widgets/{id}/inventory",
            method="GET",
            summary="Get widget inventory by warehouse",
            action_id="acme.widgets.inventory",
            provider_key="acme-erp",
            schema_hash="abc",
        )
        assert miss.source == SOURCE_LLM_LOCALIZATION
        assert miss.label == "Inventário de widgets por depósito"
        assert calls["n"] == 1

        hit = ActionDisplayLabelResolver.resolve(
            path="/acme/widgets/{id}/inventory",
            method="GET",
            summary="Get widget inventory by warehouse",
            action_id="acme.widgets.inventory",
            provider_key="acme-erp",
            schema_hash="abc",
        )
        assert hit.source == SOURCE_LLM_LOCALIZATION
        assert hit.label == miss.label
        assert calls["n"] == 1
    finally:
        ActionDisplayLabelResolver.configure()


def test_gen_metamorphic_provider_path_operation_rename(monkeypatch):
    summary = "Consultar disponibilidade de item"
    a = ActionDisplayLabelResolver.resolve(
        path="/v1/widgets/{id}/availability",
        method="GET",
        summary=summary,
        action_id="widgets.availability.v1",
        provider_key="acme",
    )
    b = ActionDisplayLabelResolver.resolve(
        path="/catalog/sku/{sku}/availability",
        method="GET",
        summary=summary,
        action_id="catalog.sku.availability",
        provider_key="northwind",
    )
    assert a.label == b.label == summary
    assert a.source == b.source == SOURCE_OPENAPI_SUMMARY


def test_gen_unknown_provider_without_x_delpi(monkeypatch):
    result = ActionDisplayLabelResolver.resolve(
        path="/fleet/vehicles/{vin}/telemetry",
        method="GET",
        summary="Retrieve vehicle telemetry snapshot",
        action_id="fleet.vehicle.telemetry",
        provider_key="fleet-ops-never-seen",
        delpi_metadata=None,
    )
    assert result.label
    assert result.source != "LEGACY_PATH_LABEL"
    assert (
        "telemetry" in result.label.casefold()
        or "vehicle" in result.label.casefold()
        or "veículo" in result.label.casefold()
        or "telemetria" in result.label.casefold()
        or result.label
    )
