"""Compliance descrição cadastral × Normas Técnicas DELPI."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_product_family_classification_service import (
    ChatDrawingProductFamilyClassificationService,
)
from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from app.domain.services.chat_technical_description_compliance_service import (
    OUTCOME_EVALUATE,
    OUTCOME_MISSING_DOCS,
    OUTCOME_NEED_CONTEXT,
    ChatTechnicalDescriptionComplianceService,
)
from app.domain.services.chat_technical_description_intent_service import (
    ChatTechnicalDescriptionIntentService,
)

configure_domain_infrastructure_ports()


def _workspace_with_product(
    code: str,
    *,
    preview: str,
) -> dict:
    return {
        "workingMemory": {
            "operationalFocus": {"productCode": code},
            "lastResultExcerpt": {
                "preview": preview,
                "topKeys": [code],
            },
        }
    }


def test_is_compliance_follow_up_markers():
    assert ChatTechnicalDescriptionComplianceService.is_compliance_follow_up(
        "está dentro das normas?"
    )
    assert ChatTechnicalDescriptionComplianceService.is_compliance_follow_up(
        "a descrição está conforme as normas técnicas?"
    )
    assert not ChatTechnicalDescriptionComplianceService.is_compliance_follow_up(
        "qual a descrição do produto 10080047"
    )


def test_finished_product_missing_normas_docs():
    ws = _workspace_with_product(
        "90260140",
        preview="O produto **90260140**\nCabo acabado exemplo XYZ",
    )
    assessment = ChatTechnicalDescriptionComplianceService.assess(
        "está dentro das normas?",
        workspace_context=ws,
    )

    assert assessment is not None
    assert assessment.outcome == OUTCOME_MISSING_DOCS
    assert assessment.family_kind == ChatDrawingProductFamilyClassificationService.KIND_FINISHED
    assert assessment.has_normas_documentation is False
    assert assessment.direct_answer
    assert "produto acabado" in assessment.direct_answer.lower()
    assert "1001" in assessment.direct_answer or "50xx" in assessment.direct_answer


def test_raw_material_evaluate_when_description_present():
    ws = _workspace_with_product(
        "10080047",
        preview=(
            "O produto **10080047**\n"
            "Descrição: TERM. OLHAL M4 3,40MM 1,00-2,50MM2 ESTANHADO"
        ),
    )
    assessment = ChatTechnicalDescriptionComplianceService.assess(
        "está conforme as normas?",
        workspace_context=ws,
    )

    assert assessment is not None
    assert assessment.outcome == OUTCOME_EVALUATE
    assert assessment.has_normas_documentation is True
    assert assessment.description_text
    assert "TERM" in assessment.description_text.upper() or "OLHAL" in (
        assessment.description_text or ""
    ).upper()
    assert assessment.direct_answer is None
    rag_q = ChatTechnicalDescriptionComplianceService.build_rag_query(
        "está conforme as normas?",
        workspace_context=ws,
    )
    assert rag_q
    assert "1008" in rag_q or "Normas" in rag_q


def test_intermediate_evaluate():
    ws = _workspace_with_product(
        "50232222",
        preview="50232222 CB1,50VERD-00255/06/06-6314-0111",
    )
    assessment = ChatTechnicalDescriptionComplianceService.assess(
        "essa descrição está dentro das normas?",
        workspace_context=ws,
    )

    assert assessment is not None
    assert assessment.outcome == OUTCOME_EVALUATE
    assert (
        assessment.family_kind
        == ChatDrawingProductFamilyClassificationService.KIND_INTERMEDIATE
    )
    rag_q = ChatTechnicalDescriptionComplianceService.build_rag_query(
        "essa descrição está dentro das normas?",
        workspace_context=ws,
    )
    assert rag_q
    assert "50xx" in rag_q or "intermediário" in rag_q.lower() or "intermediate" in rag_q.lower()
    assert "Normas_Tecnicas_DELPI" not in rag_q
    assert "1008" not in rag_q


def test_need_context_without_product():
    assessment = ChatTechnicalDescriptionComplianceService.assess(
        "está dentro das normas?",
        workspace_context={"workingMemory": {}},
    )

    assert assessment is not None
    assert assessment.outcome == OUTCOME_NEED_CONTEXT
    assert assessment.direct_answer


def test_requires_normas_only_when_evaluate():
    ws_mp = _workspace_with_product(
        "10080047",
        preview="Descrição: TERM. OLHAL M4 1,00-2,50MM2 ESTANHADO GRANEL",
    )
    ws_pa = _workspace_with_product(
        "90260140",
        preview="Descrição: PRODUTO ACABADO EXEMPLO",
    )

    assert ChatTechnicalDescriptionIntentService.requires_normas_knowledge(
        "está dentro das normas?",
        workspace_context=ws_mp,
    )
    assert not ChatTechnicalDescriptionIntentService.requires_normas_knowledge(
        "está dentro das normas?",
        workspace_context=ws_pa,
    )
    assert not ChatTechnicalDescriptionIntentService.requires_normas_knowledge(
        "está dentro das normas?",
    )


def test_classify_compliance_pa_direct_answer():
    ws = _workspace_with_product(
        "90260140",
        preview="Descrição: PA exemplo",
    )
    route = ChatIntentRouterService.classify(
        "está dentro das normas?",
        workspace_context=ws,
    )

    assert route.decision == "direct_answer"
    assert "unavailable" in str(route.sub_intent or "")
    assert route.requires_rag is False


def test_classify_compliance_mp_rag():
    ws = _workspace_with_product(
        "10080047",
        preview="Descrição: TERM. OLHAL M4 1,00-2,50MM2 ESTANHADO",
    )
    route = ChatIntentRouterService.classify(
        "está conforme as normas?",
        workspace_context=ws,
    )

    assert route.decision == "rag_internal"
    assert route.sub_intent == "technical_description_compliance"
    assert route.requires_rag is True


def test_resolve_description_from_tool_calls_payload():
    previous = [
        {
            "role": "assistant",
            "content": "O produto **10080047**\n\nTotal de **ipi_rate**: **0**.",
            "toolCalls": [
                {
                    "metadata": {
                        "path": "/products/10080047",
                        "responsePreview": {
                            "data": {
                                "product": {
                                    "code": "10080047",
                                    "description": (
                                        "TERM. PINO RETO 20-14AWG COMP 19,90MM "
                                        "ESTANHADO S/ISOLACAO CARRETEL"
                                    ),
                                }
                            }
                        },
                    }
                }
            ],
        }
    ]
    desc = ChatTechnicalDescriptionComplianceService._resolve_description_text(
        previous_messages=previous,
        workspace_context={
            "workingMemory": {
                "operationalFocus": {"productCode": "10080047"},
                "lastResultExcerpt": {
                    "preview": "O produto **10080047**\nTotal de **ipi_rate**: **0**."
                },
            }
        },
        product_code="10080047",
    )
    assert desc is not None
    assert "TERM" in desc.upper()
    assert "ipi" not in desc.lower()
