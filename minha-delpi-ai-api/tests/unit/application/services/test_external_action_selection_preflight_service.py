from unittest.mock import MagicMock

from app.application.services.external_actions.external_action_selection_preflight_service import (
    ExternalActionSelectionPreflightService,
)


def test_custom_sql_authoring_skips_system_metadata_preflight():
    route_selection = MagicMock()

    result = ExternalActionSelectionPreflightService.try_sql_authoring_system_metadata(
        (
            "use sql para construir uma query que liste 5 produtos "
            "na tabela de produtos, grupo 1008"
        ),
        route_selection=route_selection,
        allowed_action_ids=["system-search"],
        candidates_loader=MagicMock(),
    )

    assert result == "skip"
    route_selection.select_system_metadata.assert_not_called()
