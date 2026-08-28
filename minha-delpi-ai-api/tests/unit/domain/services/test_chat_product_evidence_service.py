"""Currency ≠ SKU e productEvidence para compare de estrutura."""

from __future__ import annotations

from app.application.services.chat_structure_comparison_orchestration_service import (
    ChatStructureComparisonOrchestrationService,
)
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_product_evidence_service import ChatProductEvidenceService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


def test_currency_excerpt_yields_zero_product_codes():
    text = "ROL consolidado: R$ 655.120,74 na filial 01"
    assert ChatProductQueryIntentService.extract_product_code(text) is None
    assert ChatAnalysisIntentService.extract_all_product_codes(text) == []


def test_real_product_codes_still_extracted():
    codes = ChatAnalysisIntentService.extract_all_product_codes(
        "comparar estrutura 10080047 e 10080055"
    )
    assert codes == ["10080047", "10080055"]
    assert ChatProductEvidenceService.has_product_evidence(
        "comparar estrutura 10080047 e 10080055"
    )


def test_temporal_compare_without_product_evidence_skips_bom():
    selection = type(
        "Sel",
        (),
        {
            "select_action_for_product": staticmethod(
                lambda *a, **k: {"actionId": "should-not-run"}
            )
        },
    )()

    planned = ChatStructureComparisonOrchestrationService.plan_structure_fetches(
        selection,
        message="comparar com ano anterior no mesmo periodo",
        allowed_action_ids=["product-structure"],
        previous_messages=[
            {
                "role": "assistant",
                "metadata": {
                    "toolCalls": [
                        {
                            "name": "execute_external_action",
                            "arguments": {
                                "parameters": {
                                    "start_date": "01-08-2026",
                                    "end_date": "28-08-2026",
                                }
                            },
                            "metadata": {
                                "ok": True,
                                "path": "/financial/rol",
                                "apiRouteDomain": "financial_kpi",
                                "requestParameters": {
                                    "start_date": "01-08-2026",
                                    "end_date": "28-08-2026",
                                },
                            },
                        }
                    ]
                },
            }
        ],
    )

    assert planned == []
    assert not ChatProductEvidenceService.has_product_evidence(
        "comparar com ano anterior",
        last_action={
            "path": "/financial/rol",
            "apiRouteDomain": "financial_kpi",
            "params": {"start_date": "01-08-2026"},
        },
    )


def test_two_codes_in_message_keeps_structure_plan():
    class Sel:
        def __init__(self):
            self.calls = []

        def select_action_for_product(self, message, *, product_code, allowed_action_ids=None, intent=None):
            self.calls.append(product_code)
            return {
                "name": "execute_external_action",
                "arguments": {"actionId": "product-structure", "parameters": {"code": product_code}},
                "reason": "estrutura",
            }

    selection = Sel()
    planned = ChatStructureComparisonOrchestrationService.plan_structure_fetches(
        selection,
        message="comparar estrutura do 10080047 com 10080055",
        allowed_action_ids=["product-structure"],
        previous_messages=[],
    )

    assert len(planned) == 2
    assert set(selection.calls) == {"10080047", "10080055"}
