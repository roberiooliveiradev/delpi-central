import pytest
import re
from datetime import date
from unittest.mock import patch
from app.application.services.chat_intelligence_pipeline_service import (
    ChatIntelligencePipelineService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)
from app.domain.services.chat_external_action_direct_answer_service import (
    ChatExternalActionDirectAnswerService,
)
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_operational_parameter_service import (
    ChatOperationalParameterService,
)
from app.domain.services.chat_operational_pipeline_service import (
    ChatOperationalPipelineService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_drawing_intent_service import ChatDrawingIntentService
from tests.fixtures.production_operational_regression_cases import (
    PRODUCTION_OPERATIONAL_SELECTION_CASES,
)
from tests.fixtures.chat_intelligence_regression_cases import (
    AGENTIC_SKIP_REFINEMENT_CASES,
    ANALYSIS_INTENT_CASES,
    DRAWING_CONTEXT_INTELLIGENCE_CASES,
    DRAWING_INTENT_CASES,
    DATA_INTERPRETATION_CASES,
    DATA_INTERPRETATION_NO_ACTION_CASES,
    DATA_INTERPRETATION_SKIP_TOOLS_CASES,
    DATE_RANGE_SELECTION_CASES,
    DIRECT_ANSWER_CASES,
    INTENT_CASES,
    METRIC_REFINEMENT_SELECTION_CASES,
    MISSING_PRODUCT_CODE_CASES,
    MULTI_TURN_INTENT_CASES,
    MULTI_TURN_PRODUCT_CODE_CASES,
    OPERATIONAL_FAST_PATH_CASES,
    OPERATIONAL_REFINEMENT_FAST_PATH_CASES,
    OPERATIONAL_QUALITY_JUN2026_CASES,
    PAGINATION_REFINEMENT_SELECTION_CASES,
    PRESENTER_HUMANIZED_CASES,
    PRODUCT_CODE_CASES,
    QUERY_IMPROVEMENT_CASES,
    SELECTION_CASES,
    SIMPLE_TURN_GATE_CASES,
    STOCK_REFINEMENT_SELECTION_CASES,
    UNCLEAR_REQUEST_CASES,
    HYBRID_ORCHESTRATION_CASES,
)
from app.domain.services.chat_simple_turn_gate_service import (
    ChatSimpleTurnGateService,
)
from app.domain.services.chat_unclear_request_service import (
    ChatUnclearRequestService,
)


class FakeRepository:
    def __init__(self, actions):
        self.actions = actions

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        return self.actions

    def list_actions(self):
        return self.actions


def setup_module() -> None:
    configure_domain_infrastructure_ports()


@pytest.mark.parametrize("message,expected_intent", INTENT_CASES)
def test_intent_regression(message, expected_intent):
    assert ChatProductQueryIntentService.detect(message) == expected_intent


@pytest.mark.parametrize("message,expected", DRAWING_INTENT_CASES)
def test_drawing_intent_regression(message, expected):
    assert (
        ChatDrawingIntentService.is_drawing_analysis_request(
            message,
            attachment_ids=["att-smoke"] if expected else None,
        )
        is expected
    )


@pytest.mark.parametrize("case", DRAWING_CONTEXT_INTELLIGENCE_CASES, ids=lambda c: c["id"])
def test_drawing_context_intelligence_regression(case):
    from app.domain.services.chat_agentic_catalog_service import ChatAgenticCatalogService
    from app.domain.services.chat_intent_router.chat_intent_router_classify_service import (
        ChatIntentRouterClassifyService,
    )
    from app.domain.services.chat_tool_parameter_grounding_service import (
        ChatToolParameterGroundingService,
    )

    if "expect_intent" in case:
        route = ChatIntentRouterClassifyService.classify(case["message"])
        assert route.intent == case["expect_intent"]
        assert route.requires_llm is case["expect_requires_llm"]
        return

    action = {
        "actionId": "api_delpi.products.get_product_drawing",
        "path": "/products/{code}/drawing",
        "method": "GET",
        "parametersSchema": [{"name": "code", "in": "path", "required": True}],
    }
    grounded = ChatToolParameterGroundingService.ground_parameters(
        action,
        {},
        message=case["message"],
        memory_snapshot=case.get("memory_snapshot"),
    )
    expected_code = case.get("expect_grounded_code")

    if expected_code:
        assert grounded.get("code") == expected_code
    else:
        assert not grounded.get("code")

    if case.get("expect_catalog_empty"):
        class _Repo:
            def find_candidate_actions(self, message, limit=12, allowed_action_ids=None):
                return [action]

        slim = ChatAgenticCatalogService.build_slim_catalog(
            case["message"],
            [action["actionId"]],
            _Repo(),
            memory_snapshot=case.get("memory_snapshot"),
        )
        assert slim == []


@pytest.mark.parametrize("case", PRODUCT_CODE_CASES)
def test_product_code_regression(case):
    if len(case) == 2:
        message, expected = case
        context = None
    else:
        message, expected, context = case

    assert ChatProductQueryIntentService.resolve_product_code(message, context) == expected


@pytest.mark.parametrize("message,expected", ANALYSIS_INTENT_CASES)
def test_analysis_intent_regression(message, expected):
    assert (
        ChatAnalysisIntentService.is_comparison_or_insight_request(message) is expected
    )


@pytest.mark.parametrize("message,history,expected", DATA_INTERPRETATION_CASES)
def test_data_interpretation_intent_regression(message, history, expected):
    assert (
        ChatAnalysisIntentService.is_data_interpretation_request(message, history)
        is expected
    )


@pytest.mark.parametrize("message,history,expected", DATA_INTERPRETATION_SKIP_TOOLS_CASES)
def test_data_interpretation_skip_tools_regression(message, history, expected):
    assert (
        ChatOperationalParameterService.should_skip_tools(
            message,
            previous_messages=history,
        )
        is expected
    )


@pytest.mark.parametrize("case", DATA_INTERPRETATION_NO_ACTION_CASES)
def test_data_interpretation_does_not_select_action(case):
    service = ExternalActionSelectionService(FakeRepository(case["actions"]))
    allowed = [action["actionId"] for action in case["actions"]]

    selected = service.select_action(
        case["message"],
        allowed_action_ids=allowed,
        previous_messages=case.get("previous_messages"),
    )

    assert selected is None


@pytest.mark.parametrize("message,expected", MISSING_PRODUCT_CODE_CASES)
def test_missing_product_code_regression(message, expected):
    assert (
        ChatOperationalParameterService.should_skip_tools(message) is expected
    )


@pytest.mark.parametrize("message,expected", OPERATIONAL_FAST_PATH_CASES)
def test_operational_fast_path_regression(message, expected):
    assert (
        ChatOperationalPipelineService.should_optimize(
            message,
            ["action-1"],
        )
        is expected
    )


@pytest.mark.parametrize("message,expected,history", OPERATIONAL_REFINEMENT_FAST_PATH_CASES)
def test_operational_refinement_fast_path_regression(message, expected, history):
    decisions = ChatIntelligencePipelineService.resolve_pre_tool_decisions(
        message,
        ["stock-action"],
        previous_messages=history,
    )

    assert decisions.operational_optimize is expected


@pytest.mark.parametrize("message,expected,history", AGENTIC_SKIP_REFINEMENT_CASES)
def test_agentic_skip_on_stock_refinement_regression(message, expected, history):
    assert (
        ChatOperationalParameterService.should_skip_agentic_loop(
            message,
            previous_messages=history,
        )
        is expected
    )


def test_agentic_skip_on_follow_up_chip_query():
    assert ChatOperationalParameterService.should_skip_agentic_loop(
        "mostre a estrutura do produto 10080001",
    )


@pytest.mark.parametrize(
    "case",
    SELECTION_CASES
    + PRODUCTION_OPERATIONAL_SELECTION_CASES
    + OPERATIONAL_QUALITY_JUN2026_CASES
    + STOCK_REFINEMENT_SELECTION_CASES
    + METRIC_REFINEMENT_SELECTION_CASES
    + PAGINATION_REFINEMENT_SELECTION_CASES,
)
def test_action_selection_regression(case):
    service = ExternalActionSelectionService(FakeRepository(case["actions"]))
    allowed = [action["actionId"] for action in case["actions"]]

    selected = service.select_action(
        case["message"],
        allowed_action_ids=allowed,
        previous_messages=case.get("previous_messages"),
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == case["expected_action_id"]

    expected_parameters = case.get("expected_parameters")

    if expected_parameters:
        params = selected["arguments"].get("parameters") or {}

        for key, value in expected_parameters.items():
            assert params.get(key) == value


_DATE_RANGE_REFERENCE = date(2026, 6, 9)


def _message_uses_relative_date(message: str) -> bool:
    normalized = message.lower()
    if re.search(r"\d{2}/\d{2}/\d{4}", normalized):
        return False

    return any(
        term in normalized
        for term in (
            "hoje",
            "essa semana",
            "nessa semana",
            "semana passada",
            "esse mes",
            "esse mês",
        )
    )


@pytest.mark.parametrize("case", DATE_RANGE_SELECTION_CASES)
def test_date_range_selection_regression(case):
    service = ExternalActionSelectionService(FakeRepository(case["actions"]))
    allowed = [action["actionId"] for action in case["actions"]]

    if _message_uses_relative_date(case["message"]):
        with patch("app.domain.services.chat_date_range_intent_service.date") as mock_date:
            mock_date.today.return_value = _DATE_RANGE_REFERENCE
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

            selected = service.select_action(
                case["message"],
                allowed_action_ids=allowed,
            )
    else:
        selected = service.select_action(
            case["message"],
            allowed_action_ids=allowed,
        )

    assert selected is not None

    if case.get("expected_action_id"):
        assert (
            selected["arguments"].get("actionId") == case["expected_action_id"]
        )

    params = selected["arguments"].get("parameters") or {}

    for key, value in case["expected_parameters"].items():
        assert params.get(key) == value


@pytest.mark.parametrize("message,expected_code,history", MULTI_TURN_PRODUCT_CODE_CASES)
def test_multi_turn_product_code_regression(message, expected_code, history):
    assert (
        ChatProductQueryIntentService.resolve_product_code(
            message,
            previous_messages=history,
        )
        == expected_code
    )


@pytest.mark.parametrize("message,expected_intent,history", MULTI_TURN_INTENT_CASES)
def test_multi_turn_intent_regression(message, expected_intent, history):
    assert (
        ChatProductQueryIntentService.resolve_product_intent(
            message,
            previous_messages=history,
        )
        == expected_intent
    )


@pytest.mark.parametrize("case", DIRECT_ANSWER_CASES)
def test_direct_answer_regression(case):
    answer = ChatExternalActionDirectAnswerService.format(
        case["humanized"],
        message=case["message"],
        path=case["path"],
        operation_id=case["operation_id"],
    )

    assert answer is not None

    for token in case["must_contain"]:
        assert token in answer


@pytest.mark.parametrize("message,expected_intent", SIMPLE_TURN_GATE_CASES)
def test_simple_turn_gate_regression(message, expected_intent):
    decision = ChatSimpleTurnGateService.evaluate(message=message)

    if expected_intent is None:
        assert decision.matched is False
        assert decision.hide_activity is False
    else:
        assert decision.matched is True
        assert decision.intent == expected_intent
        assert decision.hide_activity is True
        assert decision.requires_tool is False
        assert decision.requires_rag is False


@pytest.mark.parametrize("message,expected_category", UNCLEAR_REQUEST_CASES)
def test_unclear_request_regression(message, expected_category):
    assert ChatUnclearRequestService.classify(message) == expected_category


@pytest.mark.parametrize("case", HYBRID_ORCHESTRATION_CASES, ids=lambda c: c["id"])
def test_hybrid_orchestration_regression(case):
    from app.domain.services.chat_intent_router_service import ChatIntentRouterService
    from app.domain.services.chat_llm_synthesis_leak_guard_service import (
        ChatLlmSynthesisLeakGuardService,
    )
    from app.domain.services.chat_turn_analysis_service import ChatTurnAnalysisService

    if case.get("expect_unclear_category"):
        assert (
            ChatUnclearRequestService.classify(case["message"])
            == case["expect_unclear_category"]
        )

    if case.get("expect_classify_not_schedule"):
        route = ChatIntentRouterService.classify(case["message"])
        assert route.sub_intent != "schedule_today_lookup"

    if case.get("expect_intent"):
        route = ChatIntentRouterService.classify(case["message"])
        assert route.intent == case["expect_intent"]
        assert route.sub_intent == case.get("expect_sub_intent")
        assert route.requires_tool is case.get("expect_requires_tool", True)

    if "expect_analysis_gate" in case:
        route = ChatIntentRouterService.classify(case["message"])
        opened = ChatTurnAnalysisService.should_analyze(
            response_mode=case.get("response_mode") or "normal",
            heuristic_intent=route.intent,
            heuristic_decision=route.decision,
            heuristic_reason=route.reason,
            heuristic_confidence=route.confidence,
        )
        assert opened is case["expect_analysis_gate"]

    if case.get("expect_heuristic_skills"):
        from app.domain.services.chat_skill_composition_service import (
            ChatSkillCompositionService,
        )

        keys = ChatSkillCompositionService.infer_heuristic_skill_keys(case["message"])
        for skill in case["expect_heuristic_skills"]:
            assert skill in keys

    if case.get("expect_leak_fallback"):
        assert ChatLlmSynthesisLeakGuardService.needs_fallback(
            answer=case["leaked_answer"],
        )


@pytest.mark.parametrize("case", QUERY_IMPROVEMENT_CASES)
def test_query_improvement_regression(case):
    from app.domain.services.chat_intent_router_service import ChatIntentRouterService
    from app.domain.services.chat_user_query_improvement_service import (
        ChatUserQueryImprovementService,
    )

    class _FakeGateway:
        def __init__(self, reply: str) -> None:
            self.reply = reply

        def generate(self, messages: list[dict]) -> str:
            return self.reply

        def stream(self, messages: list[dict]):
            yield self.reply

    gateway = None
    if case.get("mock_llm_reply"):
        gateway = _FakeGateway(case["mock_llm_reply"])
    ChatUserQueryImprovementService.configure(gateway)
    improved = ChatUserQueryImprovementService.improve(
        case["message"],
        response_mode="fast",
        llm_gateway=gateway,
    )
    assert improved.applied is case["expect_applied"]
    if case.get("expect_source"):
        assert improved.source == case["expect_source"]
    if case.get("expect_improved_contains"):
        assert case["expect_improved_contains"] in improved.message_for_intelligence.lower()

    route = ChatIntentRouterService.classify(improved.message_for_intelligence)
    if case.get("expect_sub_intent"):
        assert route.sub_intent == case["expect_sub_intent"]
    if case.get("expect_product_code"):
        assert route.resolved_params.get("productCode") == case["expect_product_code"]


@pytest.mark.parametrize("case", PRESENTER_HUMANIZED_CASES)
def test_presenter_humanized_summary_regression(case):
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

    presenter = ExternalActionResultPresenter()
    humanized = presenter.present(case["payload"], path=case["path"])
    joined = "\n".join(
        [
            str(humanized.get("titulo") or ""),
            *(humanized.get("linhas") or []),
            str(humanized.get("humanizedMarkdown") or ""),
        ]
    ).lower()

    for token in case["must_contain"]:
        assert token.lower() in joined, f"faltou «{token}» em {case['label']}"
