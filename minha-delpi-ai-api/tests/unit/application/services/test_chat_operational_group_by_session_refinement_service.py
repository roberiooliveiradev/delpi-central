from unittest.mock import MagicMock

from app.application.services.chat_operational_group_by_session_refinement_service import (
    ChatOperationalGroupBySessionRefinementService,
)


def _consumption_history_with_table_rows():
    return [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "production-consumption-top-items",
                            "parameters": {"limit": 50, "group_by": "general"},
                        },
                        "metadata": {
                            "ok": True,
                            "path": "/production/consumption/top-items",
                            "actionId": "production-consumption-top-items",
                            "entity": "production_consumption_top_items",
                            "tablePresentation": {
                                "type": "table",
                                "rows": [
                                    {
                                        "item_code": "1",
                                        "unit": "PC",
                                        "real_consumption_qty": 100.0,
                                    },
                                    {
                                        "item_code": "2",
                                        "unit": "PC",
                                        "real_consumption_qty": 50.0,
                                    },
                                    {
                                        "item_code": "3",
                                        "unit": "KG",
                                        "real_consumption_qty": 20.0,
                                    },
                                ],
                            },
                        },
                    }
                ]
            },
        }
    ]


def test_resolve_turn_aggregates_unit_locally_without_api():
    external_use_case = MagicMock()
    external_use_case.build_metadata_for_data.return_value = {
        "ok": True,
        "path": "/production/consumption/top-items",
        "actionId": "production-consumption-top-items",
        "tablePresentation": {"type": "table", "rows": []},
    }

    result = ChatOperationalGroupBySessionRefinementService.resolve_turn(
        "consumo por unidade da listagem",
        previous_messages=_consumption_history_with_table_rows(),
        external_use_case=external_use_case,
    )

    assert result.kind == "success"
    assert result.payload is not None
    external_use_case.build_metadata_for_data.assert_called_once()
    _data, metadata, _arguments, _prompt = result.payload
    assert metadata.get("sessionDataRefinement", {}).get("dimension") == "unit"
    assert metadata.get("dataCoverageNotice", {}).get("kind") == "partial"


def test_resolve_turn_skips_product_group_for_refetch_path():
    result = ChatOperationalGroupBySessionRefinementService.resolve_turn(
        "agrupar por grupo",
        previous_messages=_consumption_history_with_table_rows(),
        external_use_case=MagicMock(),
    )

    assert result.kind == "skip"
