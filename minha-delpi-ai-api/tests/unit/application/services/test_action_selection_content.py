from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


def test_action_selection_heuristic_terms_exist():
    from app.domain.services.external_actions.external_action_response_content_service import (
        ExternalActionResponseContentService,
    )

    terms = ExternalActionResponseContentService.list(
        "actionSelection",
        "productQuestionTerms",
    )
    assert "estoque" not in terms
    assert "produto" in terms
    assert ExternalActionResponseContentService.list(
        "actionSelection",
        "lmpQuestion",
        "terms",
    )
    sql_terms = ExternalActionResponseContentService.list(
        "actionSelection",
        "sqlOrDataQueryTerms",
    )
    assert "sql" in sql_terms
    assert "select " in sql_terms
    assert ExternalActionResponseContentService.list(
        "actionSelection",
        "productSearch",
        "searchTriggers",
    )
    assert ExternalActionResponseContentService.list(
        "actionSelection",
        "kpiQuestions",
        "cpvTerms",
    )
    assert ExternalActionResponseContentService.get(
        "actionSelection",
        "productionOeeAppointmentPath",
    )
    assert ExternalActionResponseContentService.get(
        "actionSelection",
        "productionEficienciaFabrilDashboardPath",
    )
    assert ExternalActionResponseContentService.get(
        "actionSelection",
        "productionEficienciaFabrilDashboardOperationId",
    )
    appointment_terms = ExternalActionResponseContentService.list(
        "actionSelection",
        "productionOeeAppointmentTerms",
    )
    assert "roteiro do apontamento" in appointment_terms
    fabril_terms = ExternalActionResponseContentService.list(
        "actionSelection",
        "productionEficienciaFabrilTerms",
    )
    assert "eficiencia fabril" in fabril_terms


def test_selection_reasons_keys_exist():
    keys = (
        "saleOrdersList",
        "transformaMais",
        "systemMetadata",
        "productSearchByGroup",
        "productSearchByDescription",
        "paginationRefinementDefault",
        "genericSemanticFallback",
        "lmpQuery",
        "kpiCpv",
        "kpiStockValue",
        "kpiProductionOeeDetail",
        "kpiEficienciaFabrilDashboard",
        "semanticRankReason",
    )

    for key in keys:
        value = ExternalActionResponseContentService.get("selectionReasons", key)
        assert value, f"missing selectionReasons.{key}"


def test_rag_activity_stream_keys_exist():
    assert ChatAssistantContentService.get(
        "stream",
        "activity",
        "rag",
        "searching",
        "message",
    )
    assert ChatAssistantContentService.format(
        "stream",
        "activity",
        "rag",
        "foundSources",
        "messageTemplate",
        count=3,
    )
