"""Schema native do tv_dashboard_copilot enriquecido pelo catálogo BFF."""

from __future__ import annotations

from app.application.services.chat_native_tool_schema_service import (
    ChatNativeToolSchemaService,
)


class _Tool:
    name = "tv_dashboard_copilot"
    description = "Copiloto TV base."


def test_enrich_tv_schema_from_catalog_injects_ops_and_when_to_use():
    service = ChatNativeToolSchemaService()
    catalog = {
        "catalogVersion": "test.1",
        "capabilities": [
            {
                "key": "slide_text",
                "op": "upsert_block",
                "whenToUse": "Quando o usuário pedir texto no slide.",
            },
            {
                "key": "fake_only_in_bff",
                "op": "duplicate_slide",
                "whenToUse": "Duplicar o slide atual.",
            },
        ],
    }
    schemas = service.build_openai_tools(
        allowed_tool_names=["tv_dashboard_copilot"],
        tools_registry={"tv_dashboard_copilot": _Tool()},
        tv_capability_catalog=catalog,
    )
    assert len(schemas) == 1
    fn = schemas[0]["function"]
    assert "catalogVersion" in fn["description"] or "test.1" in fn["description"]
    assert "duplicate_slide" in fn["description"]
    assert "upsert_block" in fn["parameters"]["properties"]["ops"]["description"]
    assert "duplicate_slide" in fn["parameters"]["properties"]["ops"]["description"]


def test_enrich_tv_schema_without_catalog_keeps_base_description():
    service = ChatNativeToolSchemaService()
    schemas = service.build_openai_tools(
        allowed_tool_names=["tv_dashboard_copilot"],
        tools_registry={"tv_dashboard_copilot": _Tool()},
        tv_capability_catalog=None,
    )
    assert schemas[0]["function"]["description"] == "Copiloto TV base."
