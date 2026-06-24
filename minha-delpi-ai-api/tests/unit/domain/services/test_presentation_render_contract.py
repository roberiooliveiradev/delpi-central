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


def test_prune_attaches_render_hints_without_preexisting_stack_plan():
    metadata = {
        "textPresentation": {"markdown": "### OK\n\nTexto."},
        "presentationDecision": {"layoutMode": "single", "selected": "text"},
    }

    ChatPresentationPayloadPruningService.prune(metadata)

    plan = metadata["stackPresentationPlan"]
    hints = plan["renderHints"]

    assert isinstance(plan, dict)
    assert hints["textRenderMode"] == "full"
    assert hints["tailVisualPolicy"] == "legacy"


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


def test_render_plan_skips_data_answer_decision_when_llm_prose_decoupled():
    metadata = {
        "llmProseDecoupled": True,
        "dataOnlyPresentation": True,
        "presentationDecision": {
            "layoutMode": "stack",
            "proseSource": "llm",
        },
        "stackPresentationPlan": {
            "narrativeOrder": ["lead", "profileTables"],
        },
        "dataAnswer": {
            "profileKey": "analyser",
            "summary": {"answer": "Foram retornados **14** registros."},
        },
        "tablePresentations": [
            {
                "type": "table",
                "role": "profile",
                "title": "Produto 10080024",
                "rows": [{"campo": "Código", "valor": "10080024"}],
            }
        ],
    }

    ChatPresentationRenderPlanService.build(metadata)

    segments = metadata["renderPlan"]["segments"]
    lead_segments = [segment for segment in segments if segment.get("slot") == "lead"]

    assert lead_segments == [
        {"kind": "markdown", "slot": "lead", "source": "assistantMessage"},
    ]
    assert not any(segment.get("source") == "dataAnswer" for segment in segments)
    assert any(
        segment.get("kind") == "table" and segment.get("source") == "tablePresentations"
        for segment in segments
    )


def test_render_plan_appends_profile_table_when_llm_decoupled_and_narrative_lead_only():
    metadata = {
        "llmProseDecoupled": True,
        "dataOnlyPresentation": True,
        "presentationDecision": {
            "layoutMode": "stack",
            "presentationMode": "summary_then_evidence",
            "selected": "table",
            "proseSource": "llm",
        },
        "stackPresentationPlan": {
            "presentationMode": "summary_then_evidence",
            "narrativeOrder": ["lead"],
            "sectionVisibility": {
                "profile": False,
                "guide": False,
                "structure": False,
            },
        },
        "tablePresentations": [
            {
                "type": "table",
                "role": "profile",
                "title": "Produto 10080045",
                "rows": [{"campo": "Código", "valor": "10080045"}],
            }
        ],
    }

    ChatPresentationRenderPlanService.build(metadata)

    segments = metadata["renderPlan"]["segments"]

    assert any(segment.get("kind") == "table" for segment in segments)
    assert segments[0]["source"] == "assistantMessage"


def test_render_plan_falls_back_to_lead_markdown_when_stack_segments_empty():
    metadata = {
        "presentationDecision": {"layoutMode": "stack", "selected": "text"},
        "textPresentation": {"markdown": "### Produto\n\nResumo curto."},
    }

    ChatPresentationRenderPlanService.build(metadata)

    segments = metadata["renderPlan"]["segments"]

    assert segments == [
        {"kind": "markdown", "slot": "lead", "source": "textPresentation"},
    ]


def test_factory_auto_reference_metadata_has_compact_prose_without_embeds():
    from app.application.use_cases.execute_external_action_use_case import (
        ExecuteExternalActionUseCase,
    )
    from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta
    from tests.fixtures.presentation_render_plan_gate import (
        P6_EXTENDED_PIPELINE_CASES,
        _markdown_embed_issues,
    )

    case = next(item for item in P6_EXTENDED_PIPELINE_CASES if item["id"] == "factory_status_auto_reference")
    use_case = ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )
    envelope = load_api_delpi_fixture_with_meta(case["fixture"])
    metadata = use_case._build_presentation_metadata(
        action={"path": case["path"]},
        sanitized_data=envelope,
        resolved_path=case["path"],
        request_parameters={},
    )
    markdown = str((metadata.get("textPresentation") or {}).get("markdown") or "")

    assert metadata.get("dashboardPresentation") is None
    assert metadata.get("presentation", {}).get("type") in {"markdown", "table", "kpi"}
    assert markdown.strip()
    render_hints = (metadata.get("stackPresentationPlan") or {}).get("renderHints") or {}
    assert render_hints.get("textRenderMode") in {"compact", "full"}


def test_render_plan_includes_dashboard_from_presentation_slot_on_explicit_panel():
    metadata = {
        "explicitSessionFormat": "dashboard",
        "preferredFormat": "dashboard",
        "presentationDecision": {
            "selected": "dashboard",
            "layoutMode": "stack",
            "availableViews": ["text", "dashboard", "kpi"],
        },
        "presentation": {"type": "dashboard", "title": "Painel fabril", "panels": []},
        "kpiPresentation": {"type": "kpi", "title": "Indicadores", "cards": []},
        "textPresentation": {"markdown": "### Status\n\nLead curto."},
        "stackPresentationPlan": {
            "tailVisualPolicy": "allowlist",
            "tailVisualOrder": ["kpi", "dashboard"],
            "narrativeOrder": ["lead", "tailVisuals"],
        },
    }

    from app.domain.services.chat_presentation_render_pipeline_service import (
        ChatPresentationRenderPipelineService,
    )

    ChatPresentationRenderPipelineService.finalize(metadata)

    render_plan = metadata["renderPlan"]

    assert render_plan["layoutMode"] == "single"
    assert any(
        segment.get("kind") == "dashboard" and segment.get("source") == "presentation"
        for segment in render_plan.get("segments") or []
    )
    assert metadata.get("kpiPresentation") is not None


def test_render_pipeline_finalize_prunes_and_builds_render_plan():
    metadata = {
        "presentationDecision": {
            "presentationMode": "summary_then_evidence",
            "layoutMode": "stack",
        },
        "stackPresentationPlan": {
            "presentationMode": "summary_then_evidence",
            "tailVisualPolicy": "allowlist",
            "tailVisualOrder": ["tree"],
            "narrativeOrder": ["lead", "tailVisuals"],
        },
        "treePresentation": {"type": "tree", "title": "Estrutura", "root": {"id": "1"}},
        "dashboardPresentation": {"type": "dashboard", "title": "Painel", "panels": []},
        "textPresentation": {"markdown": "### Status\n\nResumo."},
    }

    from app.domain.services.chat_presentation_render_pipeline_service import (
        ChatPresentationRenderPipelineService,
    )

    ChatPresentationRenderPipelineService.finalize(metadata)

    assert metadata.get("dashboardPresentation") is None
    render_plan = metadata.get("renderPlan")
    assert isinstance(render_plan, dict)
    assert render_plan.get("version") == 1
    assert any(segment.get("kind") == "tree" for segment in render_plan.get("segments") or [])


def test_render_plan_explicit_modes_include_primary_visual_segment():
    from app.domain.services.chat_presentation_render_pipeline_service import (
        ChatPresentationRenderPipelineService,
    )

    cases = [
        (
            "table",
            {"type": "table", "title": "Estoque", "rows": []},
            "tablePresentation",
        ),
        (
            "tree",
            {"type": "tree", "title": "Estrutura", "root": {"id": "1"}},
            "treePresentation",
        ),
        (
            "chart",
            {"type": "chart", "title": "Saldo", "data": []},
            "chartPresentation",
        ),
    ]

    for explicit, promoted, slot_key in cases:
        metadata = {
            "explicitSessionFormat": explicit,
            "preferredFormat": explicit,
            "presentationDecision": {
                "selected": explicit,
                "layoutMode": "stack",
                "availableViews": ["text", explicit, "dashboard"],
            },
            "presentation": promoted,
            "textPresentation": {"markdown": "### Status\n\nLead curto."},
            slot_key: None,
            "stackPresentationPlan": {
                "tailVisualPolicy": "allowlist",
                "tailVisualOrder": [explicit],
                "narrativeOrder": ["lead", "tailVisuals"],
            },
        }

        ChatPresentationRenderPipelineService.finalize(metadata)

        render_plan = metadata["renderPlan"]

        assert render_plan["layoutMode"] == "single", explicit
        assert any(
            segment.get("kind") == explicit and segment.get("source") == "presentation"
            for segment in render_plan.get("segments") or []
        ), explicit


def test_render_plan_explicit_table_from_table_presentations_bundle():
    from app.domain.services.chat_presentation_render_pipeline_service import (
        ChatPresentationRenderPipelineService,
    )

    metadata = {
        "explicitSessionFormat": "table",
        "preferredFormat": "table",
        "presentationDecision": {
            "selected": "table",
            "layoutMode": "stack",
            "availableViews": ["text", "table"],
        },
        "tablePresentations": [
            {"type": "table", "title": "Estoque", "columns": [], "rows": []},
        ],
        "textPresentation": {"markdown": "### Estoque\n\nResumo."},
    }

    ChatPresentationRenderPipelineService.finalize(metadata)

    segments = metadata["renderPlan"]["segments"]

    assert metadata["renderPlan"]["layoutMode"] == "single"
    assert any(
        segment.get("kind") == "table" and segment.get("source") == "tablePresentations"
        for segment in segments
    )


def test_render_plan_explicit_table_emits_operational_tables_for_multi_table_bundle():
    from app.domain.services.chat_presentation_render_pipeline_service import (
        ChatPresentationRenderPipelineService,
    )

    metadata = {
        "explicitSessionFormat": "table",
        "preferredFormat": "table",
        "presentationDecision": {
            "selected": "table",
            "layoutMode": "stack",
            "availableViews": ["text", "table"],
        },
        "presentation": {
            "type": "table",
            "title": "Fornecedores por matéria-prima",
            "columns": [],
            "rows": [{"supplier_code": "1"}],
        },
        "tablePresentations": [
            {
                "type": "table",
                "title": "Estrutura do produto (BOM)",
                "role": "structure",
                "columns": [],
                "rows": [{"component_code": "1"}],
            },
            {
                "type": "table",
                "title": "Fornecedores por matéria-prima",
                "role": "list",
                "columns": [],
                "rows": [{"supplier_code": "1"}],
            },
            {
                "type": "table",
                "title": "Última compra por matéria-prima",
                "role": "list",
                "columns": [],
                "rows": [{"invoice_number": "1"}],
            },
        ],
        "textPresentation": {"markdown": "### Diretivas\n\nResumo."},
    }

    ChatPresentationRenderPipelineService.finalize(metadata)

    segments = metadata["renderPlan"]["segments"]
    table_segments = [segment for segment in segments if segment.get("kind") == "table"]

    assert metadata["renderPlan"]["layoutMode"] == "single"
    assert table_segments == [
        {
            "kind": "table",
            "slot": "operationalTables",
            "source": "tablePresentations",
        },
    ]


def test_render_plan_explicit_text_mode_uses_stack_with_markdown():
    from app.domain.services.chat_presentation_render_pipeline_service import (
        ChatPresentationRenderPipelineService,
    )

    metadata = {
        "explicitSessionFormat": "text",
        "preferredFormat": "text",
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "single",
            "availableViews": ["text", "table", "tree"],
            "visualOrder": ["text", "table", "tree"],
        },
        "textPresentation": {"markdown": "### Produto\n\nNarrativa longa."},
        "tablePresentation": {"type": "table", "title": "Detalhes", "rows": []},
        "treePresentation": {"type": "tree", "title": "Estrutura", "root": {"id": "1"}},
        "stackPresentationPlan": {
            "tailVisualPolicy": "allowlist",
            "narrativeOrder": ["lead", "tailVisuals"],
            "tailVisualOrder": ["tree"],
        },
    }

    ChatPresentationRenderPipelineService.finalize(metadata)

    render_plan = metadata["renderPlan"]

    assert render_plan["layoutMode"] == "stack"
    assert any(segment.get("kind") == "markdown" for segment in render_plan["segments"])


def test_render_plan_explicit_canvas_mode_uses_single_markdown_only():
    from app.domain.services.chat_presentation_render_pipeline_service import (
        ChatPresentationRenderPipelineService,
    )

    metadata = {
        "explicitSessionFormat": "canvas",
        "preferredFormat": "canvas",
        "presentationDecision": {
            "selected": "canvas",
            "layoutMode": "stack",
            "availableViews": ["text", "canvas", "kpi"],
        },
        "textPresentation": {"markdown": "### Documento\n\nNarrativa para lousa."},
        "kpiPresentation": {"type": "kpi", "title": "Indicadores", "cards": []},
    }

    ChatPresentationRenderPipelineService.finalize(metadata)

    render_plan = metadata["renderPlan"]

    assert render_plan["layoutMode"] == "single"
    assert render_plan["segments"] == [
        {"kind": "markdown", "slot": "lead", "source": "textPresentation"},
    ]
