from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_llm_composition_service import (
    ChatPresentationLlmCompositionService,
)
from app.domain.services.chat_presentation_render_pipeline_service import (
    ChatPresentationRenderPipelineService,
)

configure_domain_infrastructure_ports()


def test_parse_markers_interleaves_markdown_and_components():
    segments = ChatPresentationLlmCompositionService.parse_markers(
        "Introdução.\n\n[[table]]\n\nConclusão com [[tree]]."
    )

    kinds = [item.kind for item in segments]
    assert kinds[0] == "markdown"
    assert "component" in kinds
    assert segments[1].component_kind == "table"
    assert any(item.component_kind == "tree" for item in segments)


def test_apply_builds_interleaved_render_plan():
    metadata = {
        "path": "/products/90260149/structure",
        "ok": True,
        "presentationDecision": {"layoutMode": "single", "selected": "tree"},
        "treePresentation": {"type": "tree", "title": "Estrutura", "root": {"id": "1"}},
        "tablePresentation": {
            "type": "table",
            "title": "Itens",
            "columns": ["code"],
            "rows": [{"code": "10080109"}],
        },
        "renderPlan": {
            "version": 1,
            "layoutMode": "single",
            "segments": [{"kind": "tree", "slot": "tree", "source": "treePresentation"}],
        },
    }

    cleaned = ChatPresentationLlmCompositionService.apply(
        metadata,
        "A árvore mostra a BOM.\n\n[[tree]]\n\nItens em tabela:\n\n[[table]]\n\nFim.",
        response_mode="normal",
    )

    assert "[[" not in cleaned
    assert metadata.get("proseCompositionSource") == "llm"
    plan = metadata["renderPlan"]
    assert plan["layoutMode"] == "stack"
    kinds = [seg["kind"] for seg in plan["segments"]]
    assert kinds == ["markdown", "tree", "markdown", "table", "markdown"]
    assert metadata["presentationDecision"]["proseCompositionAllowed"] is True
    assert "tree" in metadata["presentationDecision"]["allowedMarkerKinds"]


def test_apply_rejects_marker_without_slot():
    metadata = {
        "path": "/products/90260149/stock",
        "ok": True,
        "presentationDecision": {},
        "tablePresentation": {
            "type": "table",
            "title": "Estoque",
            "rows": [{"code": "1", "qty": 2}],
        },
    }

    ChatPresentationLlmCompositionService.apply(
        metadata,
        "Sem árvore disponível.\n\n[[tree]]\n\nTabela:\n\n[[table]]",
    )

    kinds = [seg["kind"] for seg in metadata["renderPlan"]["segments"]]
    assert "tree" not in kinds
    assert "table" in kinds


def test_finalize_annotates_allowed_marker_kinds():
    metadata = {
        "path": "/products/90260149/structure",
        "ok": True,
        "presentationDecision": {"layoutMode": "single", "selected": "tree"},
        "treePresentation": {"type": "tree", "title": "Estrutura", "root": {"id": "1"}},
        "textPresentation": {"markdown": "Lead."},
    }

    ChatPresentationRenderPipelineService.finalize(metadata)

    decision = metadata["presentationDecision"]
    assert decision.get("proseCompositionAllowed") is True
    assert "tree" in (decision.get("allowedMarkerKinds") or [])


def test_facts_addon_includes_composition_slots_and_rule():
    from app.domain.services.chat_operational_llm_synthesis_context_service import (
        ChatOperationalLlmSynthesisContextService,
    )

    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/90260149/structure",
                "llmProseDecoupled": True,
                "treePresentation": {"type": "tree", "title": "Estrutura", "root": {"id": "1"}},
                "dataAnswer": {"summary": {"answer": "BOM com 6 itens"}},
                "presentationDecision": {"selected": "tree"},
            },
        }
    ]

    addon = ChatOperationalLlmSynthesisContextService.build_facts_addon(
        tool_calls,
        response_mode="normal",
    )

    assert "[[tree]]" in addon or "Slots disponíveis" in addon or "slots" in addon.lower()
    assert "marcador" in addon.lower() or "composição" in addon.lower() or "Composição" in addon


def test_apply_json_fallback_prose_composition_segments():
    metadata = {
        "path": "/products/90260149/structure",
        "ok": True,
        "presentationDecision": {},
        "treePresentation": {"type": "tree", "title": "Estrutura", "root": {"id": "1"}},
        "tablePresentation": {
            "type": "table",
            "title": "Itens",
            "rows": [{"code": "10080109"}],
        },
    }
    answer = (
        'Leitura da BOM.\n'
        '{"proseComposition":{"segments":['
        '{"kind":"markdown","text":"Árvore da estrutura."},'
        '{"kind":"tree","index":1},'
        '{"kind":"markdown","text":"Tabela de itens."},'
        '{"kind":"table","index":1}'
        "]}}"
    )

    cleaned = ChatPresentationLlmCompositionService.apply(metadata, answer)

    assert metadata.get("proseCompositionSource") == "llm"
    kinds = [seg["kind"] for seg in metadata["renderPlan"]["segments"]]
    assert "tree" in kinds
    assert "table" in kinds
    assert "[[" not in cleaned


def test_enrich_multi_tool_interleaved_composition():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/90260149/structure",
                "operationId": "get_product_structure",
                "treePresentation": {"type": "tree", "title": "Estrutura", "root": {"id": "pa"}},
            },
        },
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/10080109/stock",
                "operationId": "get_product_stock",
                "tablePresentation": {
                    "type": "table",
                    "title": "Estoque MP",
                    "rows": [{"code": "10080109", "qty": 12}],
                },
            },
        },
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/10090014/stock",
                "operationId": "get_product_stock_b",
                "tablePresentation": {
                    "type": "table",
                    "title": "Estoque MP 2",
                    "rows": [{"code": "10090014", "qty": 0}],
                },
            },
        },
    ]
    primary = tool_calls[0]["metadata"]
    slots = ChatPresentationLlmCompositionService.collect_available_slots(
        primary,
        tool_calls=tool_calls,
    )
    table_slots = [slot for slot in slots if slot["kind"] == "table"]

    assert len(table_slots) >= 2
    assert {slot["index"] for slot in table_slots} >= {1, 2}

    cleaned = ChatPresentationLlmCompositionService.apply(
        primary,
        "Estrutura do PA.\n\n[[tree]]\n\nEstoque da primeira MP.\n\n[[table:1]]\n\nSegunda MP.\n\n[[table:2]]\n\nConclusão.",
        tool_calls=tool_calls,
        response_mode="normal",
    )

    assert "[[" not in cleaned
    plan = primary["renderPlan"]
    assert plan["layoutMode"] == "stack"
    kinds = [seg["kind"] for seg in plan["segments"]]
    assert kinds.count("markdown") >= 3
    assert "tree" in kinds
    assert kinds.count("table") == 2
    assert len(plan["segments"]) >= 5


def test_normal_enrich_facts_include_composition_slots_and_reminder():
    from app.composition.content_composer import configure_domain_infrastructure_ports
    from app.domain.services.chat_operational_llm_synthesis_context_service import (
        ChatOperationalLlmSynthesisContextService,
    )

    configure_domain_infrastructure_ports()

    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "llmProseDecoupled": True,
                "path": "/products/90260149/structure",
                "treePresentation": {"type": "tree", "title": "Estrutura", "root": {"id": "pa"}},
                "tablePresentation": {
                    "type": "table",
                    "title": "Itens",
                    "rows": [{"code": "10080109"}],
                },
                "presentationDecision": {"selected": "tree"},
            },
        },
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "llmProseDecoupled": True,
                "path": "/products/10080109/stock",
                "tablePresentation": {
                    "type": "table",
                    "title": "Estoque",
                    "rows": [{"code": "10080109", "qty": 0}],
                },
            },
        },
    ]

    addon = ChatOperationalLlmSynthesisContextService.build_facts_addon(
        tool_calls,
        response_mode="normal",
        tool_context={"groundedEnrichInsight": True},
    )

    assert "[[tree]]" in addon or "[[table]]" in addon or "Slots" in addon or "slots" in addon.lower()
    assert "marcador" in addon.lower() or "composição" in addon.lower() or "cruzado" in addon.lower()


def test_normal_enrich_composition_apply_builds_stack():
    metadata = {
        "ok": True,
        "path": "/products/90260149/structure",
        "treePresentation": {"type": "tree", "title": "Estrutura", "root": {"id": "pa"}},
        "tablePresentation": {
            "type": "table",
            "title": "Estoque",
            "rows": [{"code": "10080109"}],
        },
    }

    cleaned = ChatPresentationLlmCompositionService.apply(
        metadata,
        "Padrão da BOM.\n\n[[tree]]\n\nSaldos.\n\n[[table]]\n\nConclusão.",
        response_mode="normal",
    )

    assert metadata.get("proseCompositionSource") == "llm"
    assert metadata["renderPlan"]["layoutMode"] == "stack"
    assert "[[" not in cleaned
