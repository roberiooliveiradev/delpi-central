from app.domain.services.chat_presentation_evidence_first_layout_service import (
    ChatPresentationEvidenceFirstLayoutService,
)
from app.domain.services.chat_presentation_payload_pruning_service import (
    ChatPresentationPayloadPruningService,
)
from app.domain.services.chat_presentation_render_plan_service import (
    ChatPresentationRenderPlanService,
)


def test_prune_removes_dashboard_when_not_in_tail_visual_order():
    metadata = {
        "presentationDecision": {
            "presentationMode": "summary_then_evidence",
            "layoutMode": "stack",
        },
        "stackPresentationPlan": {
            "presentationMode": "summary_then_evidence",
            "tailVisualPolicy": "allowlist",
            "tailVisualOrder": ["tree", "chart"],
        },
        "treePresentation": {"type": "tree", "title": "Estrutura", "root": {"id": "1"}},
        "chartPresentation": {"type": "chart", "title": "Saldo MP", "data": []},
        "dashboardPresentation": {"type": "dashboard", "title": "Painel fabril", "panels": []},
        "kpiPresentation": {"type": "kpi", "title": "Indicadores", "cards": []},
        "textPresentation": {"markdown": "### Status\n\nSituação consolidada."},
    }

    ChatPresentationPayloadPruningService.prune(metadata)

    assert metadata.get("dashboardPresentation") is None
    assert metadata.get("kpiPresentation") is None
    assert metadata.get("treePresentation") is not None
    assert metadata.get("chartPresentation") is not None
    hints = metadata["stackPresentationPlan"]["renderHints"]
    assert hints["suppressedKinds"] == ["kpi", "dashboard"]
    assert hints["textRenderMode"] == "compact"
    assert hints["tailVisualPolicy"] == "allowlist"


def test_prune_keeps_dashboard_when_explicit_panel_session():
    metadata = {
        "explicitSessionFormat": "dashboard",
        "presentationDecision": {
            "presentationMode": "summary_then_evidence",
            "layoutMode": "stack",
        },
        "stackPresentationPlan": {
            "presentationMode": "summary_then_evidence",
            "tailVisualPolicy": "allowlist",
            "tailVisualOrder": ["dashboard"],
        },
        "dashboardPresentation": {"type": "dashboard", "title": "Painel fabril", "panels": []},
        "treePresentation": {"type": "tree", "title": "Estrutura", "root": {"id": "1"}},
        "textPresentation": {"markdown": "### Status\n\nLead curto."},
    }

    ChatPresentationPayloadPruningService.prune(metadata)

    assert metadata.get("dashboardPresentation") is not None
    assert metadata.get("treePresentation") is None
    assert metadata["stackPresentationPlan"]["renderHints"]["textRenderMode"] == "compact"


def test_prune_sets_legacy_policy_when_not_evidence_first():
    metadata = {
        "stackPresentationPlan": {
            "tailVisualOrder": ["dashboard"],
        },
        "dashboardPresentation": {"type": "dashboard", "title": "Painel", "panels": []},
        "textPresentation": {"markdown": "### Painel\n\nResumo."},
    }

    ChatPresentationPayloadPruningService.prune(metadata)

    assert metadata["stackPresentationPlan"]["tailVisualPolicy"] == "legacy"
    assert metadata.get("dashboardPresentation") is not None
    assert metadata["stackPresentationPlan"]["renderHints"]["tailVisualPolicy"] == "legacy"


def test_prune_removes_null_presentation_keys():
    metadata = {
        "stackPresentationPlan": {"tailVisualPolicy": "legacy"},
        "tablePresentation": None,
        "treePresentation": None,
        "textPresentation": {"markdown": "### OK\n\nTexto."},
    }

    ChatPresentationPayloadPruningService.prune(metadata)

    assert "tablePresentation" not in metadata
    assert "treePresentation" not in metadata


def test_prune_removes_hierarchy_duplicate_tables_when_structure_dedup_applied():
    metadata = {
        "structureDedupApplied": True,
        "stackPresentationPlan": {"tailVisualPolicy": "legacy"},
        "treePresentation": {"type": "tree", "title": "Estrutura", "root": {"id": "1"}},
        "tablePresentations": [
            {
                "type": "table",
                "title": "Componentes da estrutura",
                "columns": [{"key": "parent_code", "label": "Pai"}],
                "rows": [{"parent_code": "1"}],
            },
            {
                "type": "table",
                "title": "Estoque",
                "columns": [{"key": "branch", "label": "Filial"}],
                "rows": [{"branch": "01"}],
            },
        ],
        "textPresentation": {"markdown": "### Estrutura\n\nResumo."},
    }

    ChatPresentationPayloadPruningService.prune(metadata)

    titles = [table["title"] for table in metadata["tablePresentations"]]

    assert titles == ["Estoque"]


def test_compose_and_prune_omit_dashboard_in_automatic_summary_then_evidence():
    metadata = {
        "presentationDecision": {
            "presentationMode": "summary_then_evidence",
            "layoutMode": "stack",
        },
        "stackPresentationPlan": {
            "presentationMode": "summary_then_evidence",
            "narrativeOrder": ["lead", "operationalTables", "tailVisuals"],
            "tailVisualOrder": ["dashboard"],
        },
        "treePresentation": {"type": "tree", "title": "Estrutura", "root": {"id": "1", "children": []}},
        "chartPresentation": {"type": "chart", "title": "Saldo MP", "data": []},
        "dashboardPresentation": {"type": "dashboard", "title": "Painel fabril", "panels": []},
        "textPresentation": {"markdown": "### Status\n\nSituação consolidada."},
    }

    ChatPresentationEvidenceFirstLayoutService.compose(metadata)
    ChatPresentationPayloadPruningService.prune(metadata)
    ChatPresentationRenderPlanService.build(metadata)

    plan = metadata["stackPresentationPlan"]

    assert plan["tailVisualOrder"] == ["tree", "chart"]
    assert metadata.get("dashboardPresentation") is None
    assert metadata.get("treePresentation") is not None
    assert metadata.get("chartPresentation") is not None
    render_plan = metadata["renderPlan"]
    assert render_plan["layoutMode"] == "stack"
    assert any(segment["kind"] == "tree" for segment in render_plan["segments"])
    assert all(segment["kind"] != "dashboard" for segment in render_plan["segments"])


def test_render_plan_includes_markdown_and_tail_visuals():
    metadata = {
        "presentationDecision": {"layoutMode": "stack"},
        "stackPresentationPlan": {
            "tailVisualPolicy": "allowlist",
            "narrativeOrder": ["lead", "tailVisuals"],
            "tailVisualOrder": ["tree"],
        },
        "textPresentation": {"markdown": "### Status\n\nResumo."},
        "treePresentation": {"type": "tree", "title": "Estrutura", "root": {"id": "1"}},
    }

    ChatPresentationPayloadPruningService.prune(metadata)
    ChatPresentationRenderPlanService.build(metadata)

    segments = metadata["renderPlan"]["segments"]

    assert segments[0]["kind"] == "markdown"
    assert segments[-1]["kind"] == "tree"


def test_render_plan_includes_highlights_and_attention_when_markdown_has_sections():
    metadata = {
        "presentationDecision": {"layoutMode": "stack"},
        "stackPresentationPlan": {
            "tailVisualPolicy": "legacy",
            "narrativeOrder": ["lead", "highlights", "attention"],
        },
        "textPresentation": {
            "markdown": (
                "### Produto\n\nEscopo.\n\n**Destaques**\n\n- Item A.\n\n"
                "**Pontos de atenção encontrados na API:**\n\n1. Risco B."
            ),
        },
    }

    ChatPresentationRenderPlanService.build(metadata)

    kinds = [segment["kind"] for segment in metadata["renderPlan"]["segments"]]
    slots = [segment["slot"] for segment in metadata["renderPlan"]["segments"]]

    assert kinds.count("markdown") == 3
    assert slots == ["lead", "highlights", "attention"]


def test_render_plan_single_text_first_evidence_only_includes_prose():
    metadata = {
        "presentationDecision": {
            "presentationMode": "summary_then_evidence",
            "layoutMode": "single",
            "selected": "text",
        },
        "stackPresentationPlan": {
            "presentationMode": "summary_then_evidence",
            "tailVisualPolicy": "allowlist",
            "tailVisualOrder": ["kpi", "tree", "chart"],
            "narrativeOrder": ["lead", "operationalTables", "tailVisuals"],
        },
        "textPresentation": {"markdown": "### Status produtivo\n\nOP em andamento."},
        "kpiPresentation": {"type": "kpi", "title": "Indicadores", "items": []},
        "treePresentation": {"type": "tree", "title": "Estrutura", "root": {"id": "1"}},
        "chartPresentation": {"type": "chart", "title": "Saldo", "data": []},
        "tablePresentations": [
            {"type": "table", "title": "Ordens", "columns": [], "rows": []},
        ],
    }

    ChatPresentationEvidenceFirstLayoutService.compose(metadata)
    ChatPresentationPayloadPruningService.prune(metadata)
    ChatPresentationRenderPlanService.build(metadata)

    segments = metadata["renderPlan"]["segments"]
    kinds = {segment["kind"] for segment in segments}

    assert metadata["renderPlan"]["layoutMode"] == "single"
    assert kinds == {"markdown"}
    assert metadata.get("kpiPresentation") is not None
