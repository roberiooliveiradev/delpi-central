"""PPM por família: numerador filtrado, denominador geral."""

from unittest.mock import patch

from app.application.dto.ppm.ppm_summary_request import PpmSummaryRequest
from app.infrastructure.persistence.totvs.ppm_repositories.ppm_query_repository import (
    PpmQueryRepository,
)


def test_scoped_summary_filters_numerator_only() -> None:
    captured: dict[str, object] = {}

    def fake_execute_one(sql: str, params: tuple) -> dict:
        captured["sql"] = sql
        captured["params"] = params
        return {
            "total_devolvido_un": 10,
            "total_produzido_milheiro": 20,
            "total_produzido_un": 20000,
            "ppm": 500,
        }

    repository = PpmQueryRepository()
    request = PpmSummaryRequest(
        type="internal",
        branch="01",
        date_start="2026-07-01",
        date_end="2026-07-09",
        product_prefix="9026",
    )

    with patch.object(repository, "execute_one", side_effect=fake_execute_one):
        repository._load_summary(request)

    sql = str(captured["sql"])
    params = tuple(captured["params"])

    assert "QI2_ITEM LIKE ?" in sql
    assert "9026%" in params
    assert "SH6.H6_PRODUTO LIKE" not in sql
