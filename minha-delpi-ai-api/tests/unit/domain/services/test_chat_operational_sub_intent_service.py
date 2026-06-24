from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()

from app.domain.services.chat_intent_disambiguation_service import (  # noqa: E402
    ChatIntentDisambiguationService,
)
from app.domain.services.chat_intent_router_service import ChatIntentRouterService  # noqa: E402
from app.domain.services.chat_operational_ambiguity_service import (  # noqa: E402
    ChatOperationalAmbiguityService,
)
from app.domain.services.chat_operational_sub_intent_service import (  # noqa: E402
    ChatOperationalSubIntentService,
)


def test_operational_sub_intent_structure_exclusivity_with_product_code():
    message = "quais MPs exclusivas tem o produto 90260882?"

    assert ChatOperationalSubIntentService.resolve(message) == "structure_exclusivity_lookup"


def test_operational_ambiguity_skips_structure_exclusivity_question():
    message = "quais MPs exclusivas tem o produto 90260882?"

    ambiguous, candidates = ChatOperationalAmbiguityService.resolve(
        message,
        {"productCode": "90260882"},
    )

    assert ambiguous is False
    assert candidates == ()


def test_router_classifies_structure_exclusivity_without_ambiguity():
    message = "quais MPs exclusivas tem o produto 90260882?"
    route = ChatIntentRouterService.classify(message, allowed_action_ids=["action-1"])

    assert route.intent == "operational_query"
    assert route.sub_intent == "structure_exclusivity_lookup"
    assert route.ambiguous is False
    assert ChatIntentDisambiguationService.try_build(message, allowed_action_ids=["action-1"]) is None


def test_operational_sub_intent_pipeline_json_has_structure_exclusivity_step():
    from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

    pipeline = ChatAssistantContentService.get_node(
        "product_query_intent",
        "router",
        "operationalSubIntentPipeline",
    )

    assert isinstance(pipeline, list)
    assert any(
        isinstance(step, dict)
        and step.get("predicate") == "structureExclusivity"
        and step.get("subIntent") == "structure_exclusivity_lookup"
        for step in pipeline
    )
