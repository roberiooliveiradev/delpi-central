from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


def test_production_title_from_content():
    title = ExternalActionResponseContentService.format(
        "productionSchedule",
        "title",
        label="amanhã",
    )

    assert title == "Produtos programados para produção amanhã"


def test_weekday_label_from_content():
    assert ExternalActionResponseContentService.weekday_label(0) == "segunda-feira"
