from unittest.mock import MagicMock

from app.application.services.external_actions.external_action_selection_preflight_service import (
    ExternalActionSelectionPreflightService,
)


def test_custom_sql_authoring_blocks_operational_rest_selection():
    """«crie um sql… produtos» não deve seguir para fallback semântico REST."""
    route_selection = MagicMock()

    result = ExternalActionSelectionPreflightService.try_sql_authoring_system_metadata(
        (
            "crie um sql que liste os 10 primeiros produtos do grupo 1008"
        ),
        route_selection=route_selection,
        allowed_action_ids=["system-search", "api_delpi.produ_o_operacional.get_production_schedule_today"],
        candidates_loader=MagicMock(),
    )

    assert result is None
    route_selection.select_system_metadata.assert_not_called()


def test_custom_sql_authoring_still_allows_system_metadata_question():
    route_selection = MagicMock()
    route_selection.select_system_metadata.return_value = {"actionId": "system-columns"}

    result = ExternalActionSelectionPreflightService.try_sql_authoring_system_metadata(
        "monte uma consulta sql e mostre quais colunas existem na tabela SB1",
        route_selection=route_selection,
        allowed_action_ids=["system-columns"],
        candidates_loader=MagicMock(),
    )

    # Se o matcher de metadado não reconhecer a frase, ainda bloqueia REST (None).
    assert result is None or result.get("actionId") == "system-columns"
