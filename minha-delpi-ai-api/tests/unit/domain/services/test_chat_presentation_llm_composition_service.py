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
