from unittest.mock import MagicMock, patch

from app.application.use_cases.mini_applicators.mini_applicators_use_cases import (
    PostMiniApplicatorsGolpesBatchUseCase,
)


def test_post_mini_applicators_golpes_batch_use_case_groups_items() -> None:
    repository = MagicMock()
    repository.get_golpes_batch.return_value = [
        {
            "codigo_ferramenta": "23-001",
            "filial": "01",
            "data_inicial": "2026-01-01",
            "data_final": "2026-06-01",
            "total_golpes": 120,
        }
    ]
    use_case = PostMiniApplicatorsGolpesBatchUseCase(repository)

    result = use_case.execute(
        filial="01",
        items=[
            {
                "codigo_ferramenta": "23-001",
                "data_inicial": "2026-01-01",
                "data_final": "2026-06-01",
            }
        ],
    )

    repository.get_golpes_batch.assert_called_once_with(
        filial="01",
        items=[
            {
                "codigo_ferramenta": "23-001",
                "data_inicial": "2026-01-01",
                "data_final": "2026-06-01",
            }
        ],
    )
    assert result["total"] == 1
    assert result["items"][0]["total_golpes"] == 120
    assert result["summary"]["requested_count"] == 1


@patch("app.interface.http.routes.engineering.engineering_router.build_post_mini_applicators_golpes_batch_use_case")
def test_post_mini_applicators_golpes_batch_route_returns_meta(mock_build) -> None:
    from app.application.dto.mini_applicators.golpes_batch_request import (
        GolpesBatchItem,
        GolpesBatchRequest,
    )
    from app.interface.http.routes.engineering.engineering_router import (
        post_mini_applicators_golpes_batch_route,
    )
    from tests.test_route_phase1b_gap_smoke import assert_envelope_meta, body_json

    mock_build.return_value = MagicMock(
        execute=MagicMock(
            return_value={
                "items": [{"codigo_ferramenta": "23-001", "total_golpes": 10}],
                "total": 1,
                "summary": {"requested_count": 1, "returned_count": 1},
            }
        )
    )

    response = post_mini_applicators_golpes_batch_route(
        body=GolpesBatchRequest(
            filial="01",
            items=[
                GolpesBatchItem(
                    codigo_ferramenta="23-001",
                    data_inicial="2026-01-01",
                    data_final="2026-06-01",
                )
            ],
        )
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="post_mini_applicators_golpes_batch",
        shape="list",
    )
