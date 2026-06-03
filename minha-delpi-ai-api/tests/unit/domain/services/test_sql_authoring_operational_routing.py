"""SQL authoring não deve acionar fast path operacional nem busca de produtos."""

from app.domain.services.chat_advanced_sql_specialist_service import (
    ChatAdvancedSqlSpecialistService,
)
from app.domain.services.chat_operational_pipeline_service import (
    ChatOperationalPipelineService,
)
from app.domain.services.chat_sql_authoring_guidance_service import (
    ChatSqlAuthoringGuidanceService,
)

_USER_MESSAGE = (
    "Monte uma consulta para listar clientes ativos da tabela SA1, "
    "só código e nome, sem executar."
)

_WORKSPACE = {
    "skills": {"sqlAuthoring": True},
    "actionsEnabled": True,
    "allowedActionIds": ["system-columns", "data-sql"],
}


def test_sql_authoring_disables_operational_fast_path():
    assert not ChatOperationalPipelineService.should_optimize(
        _USER_MESSAGE,
        ["action-1"],
    )


def test_sql_authoring_not_product_search():
    from app.application.services.external_actions.external_action_selection_service import (
        ExternalActionSelectionService,
    )

    normalized = _USER_MESSAGE.lower()

    assert not ExternalActionSelectionService._looks_like_product_search(
        None,
        normalized,
    )


def test_schema_prefetch_recommended_with_agent_actions():
    assert ChatAdvancedSqlSpecialistService.should_prefetch_schema(
        message=_USER_MESSAGE,
        workspace_context=_WORKSPACE,
    )

    assert ChatSqlAuthoringGuidanceService.agent_actions_available(_WORKSPACE)
