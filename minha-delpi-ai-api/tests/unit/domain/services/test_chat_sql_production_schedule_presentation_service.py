from app.domain.services.chat_sql_production_schedule_presentation_service import (
    ChatSqlProductionSchedulePresentationService,
)
from app.domain.services.chat_sql_production_schedule_date_service import (
    ChatSqlProductionScheduleDateService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


def test_production_schedule_narrative_bundle_has_keys():
    assert ExternalActionResponseContentService.get(
        "productionSchedule",
        "narrative",
        "scopeIntro",
    )
    assert ExternalActionResponseContentService.get(
        "productionSchedule",
        "narrative",
        "largeSetHint",
    )


def test_build_linhas_includes_branch_and_preview():
    schedule = ChatSqlProductionScheduleDateService.resolve(
        "quais produtos serão produzidos hoje?"
    )
    rows = [
        {
            "FILIAL": "01",
            "COD_PRODUTO": "90264130",
            "DESCRICAO_PRODUTO": "PARAFUSO M8",
            "QTD_PLANEJADA": 1200,
            "UNIDADE": "UN",
        },
        {
            "FILIAL": "02",
            "COD_PRODUTO": "90264131",
            "DESCRICAO_PRODUTO": "PARAFUSO M10",
            "QTD_PLANEJADA": 800,
            "UNIDADE": "UN",
        },
    ]

    linhas = ChatSqlProductionSchedulePresentationService.build_linhas(
        rows,
        schedule=schedule,
        record_total=2,
        include_branch_breakdown=True,
        format_row=lambda row: str(row.get("COD_PRODUTO")),
    )

    joined = "\n".join(linhas)

    assert "hoje" in joined.lower()
    assert "filial **01**" in joined
    assert "filial **02**" in joined
    assert "9026" in joined
    assert "90264130" in joined
