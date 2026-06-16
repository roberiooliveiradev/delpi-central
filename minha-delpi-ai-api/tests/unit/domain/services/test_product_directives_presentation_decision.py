from app.domain.services.chat_presentation_decision_service import (
    ChatPresentationDecisionService,
)
from app.domain.services.chat_presentation_render_pipeline_service import (
    ChatPresentationRenderPipelineService,
)


def test_directives_automatic_mode_uses_stack_with_tabular_evidence():
    metadata = {
        "path": "/products/directives/90260882",
        "apiDelpiResponseMeta": {"entity": "product_directives"},
        "textPresentation": {
            "markdown": "### Diretivas do produto — 90260882\n\nResumo operacional.",
            "title": "Diretivas do produto — 90260882",
        },
        "tablePresentations": [
            {
                "type": "table",
                "title": "Estrutura do produto (BOM)",
                "role": "structure",
                "columns": [{"key": "component_code", "label": "Componente"}],
                "rows": [{"component_code": "50250258"}],
            },
            {
                "type": "table",
                "title": "Fornecedores por matéria-prima",
                "role": "list",
                "columns": [{"key": "supplier_code", "label": "Fornecedor"}],
                "rows": [{"supplier_code": "000052"}],
            },
            {
                "type": "table",
                "title": "Última compra por matéria-prima",
                "role": "list",
                "columns": [{"key": "invoice_number", "label": "Nº nota"}],
                "rows": [{"invoice_number": "015277"}],
            },
        ],
        "dataAnswer": {
            "profileKey": "directives",
            "summary": {
                "answer": "Consulte as tabelas abaixo.",
                "riskLevel": "ok",
            },
        },
        "availableFormats": ["text", "table", "canvas"],
    }

    ChatPresentationDecisionService.enrich_metadata(
        metadata,
        user_message="diretivas 90260882",
    )

    from app.domain.services.chat_presentation_evidence_first_layout_service import (
        ChatPresentationEvidenceFirstLayoutService,
    )
    from app.domain.services.chat_presentation_stack_order_service import (
        ChatPresentationStackOrderService,
    )

    ChatPresentationEvidenceFirstLayoutService.activate(metadata)
    ChatPresentationStackOrderService.enrich_metadata(metadata)
    ChatPresentationEvidenceFirstLayoutService.compose(metadata)
    ChatPresentationRenderPipelineService.finalize(metadata)

    decision = metadata["presentationDecision"]
    render_plan = metadata["renderPlan"]

    assert decision["layoutMode"] == "stack"
    assert decision["selected"] == "text"
    assert "sem dados tabulares" not in str(decision.get("reason") or "").lower()
    assert any(
        segment.get("kind") == "table" and segment.get("slot") == "operationalTables"
        for segment in render_plan.get("segments") or []
    )
