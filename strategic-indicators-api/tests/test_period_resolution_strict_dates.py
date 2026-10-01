"""PERF-002 — datas de período fornecidas mas inválidas devem falhar explicitamente.

Semântica alvo:
  data válida     → mesmo resultado semântico atual
  data ausente    → None (filtro/período opcional)
  data malformada → ValueError em resolve_period; helpers lenientes retornam None
"""

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from delpi_auth.request_context import reset_current_user, set_current_user
from si_app.application.services.strategic_indicators.period_resolution import (
    normalize_dashboard_period_date,
    parse_period_date,
    resolve_period,
)
from si_app.interface.http.routes.integrations_routes import router as goals_router
from si_app.interface.http.routes.strategic_indicators_routes import (
    router as main_router,
)


def test_normalize_dashboard_period_date_keeps_delpi_format() -> None:
    assert normalize_dashboard_period_date("01-10-2026") == "01-10-2026"


def test_normalize_dashboard_period_date_converts_iso_format() -> None:
    assert normalize_dashboard_period_date("2026-10-01") == "01-10-2026"


def test_parse_period_date_rejects_truncated_years() -> None:
    for malformed in ("01-10-202", "01-10-20", "01-10-2"):
        assert parse_period_date(malformed) is None, malformed


def test_parse_period_date_rejects_garbage() -> None:
    assert parse_period_date("garbage") is None


def test_parse_period_date_accepts_valid_dates() -> None:
    assert parse_period_date("01-10-2026") == date(2026, 10, 1)
    assert parse_period_date("2026-10-01") == date(2026, 10, 1)


def test_resolve_period_preserves_valid_delpi_dates() -> None:
    period = resolve_period(
        competence=None,
        start_date="01-10-2026",
        end_date="31-10-2026",
    )
    assert period.competence == "2026-10"
    assert period.start_date == "01-10-2026"
    assert period.end_date == "31-10-2026"


def test_resolve_period_preserves_valid_iso_dates() -> None:
    period = resolve_period(
        competence=None,
        start_date="2026-10-01",
        end_date="2026-10-31",
    )
    assert period.competence == "2026-10"
    assert period.start_date == "01-10-2026"
    assert period.end_date == "31-10-2026"


def test_resolve_period_rejects_truncated_years() -> None:
    for malformed in ("01-10-202", "01-10-20", "01-10-2"):
        with pytest.raises(ValueError, match="inválida"):
            resolve_period(
                competence=None,
                start_date=malformed,
                end_date="31-10-2026",
            )
        with pytest.raises(ValueError, match="inválida"):
            resolve_period(
                competence=None,
                start_date="01-10-2026",
                end_date=malformed,
            )


def test_resolve_period_rejects_garbage_and_impossible_dates() -> None:
    for malformed in ("garbage", "31-02-2026", "99-99-9999"):
        with pytest.raises(ValueError, match="inválida"):
            resolve_period(
                competence=None,
                start_date=malformed,
                end_date=None,
            )


def test_resolve_period_absent_dates_still_optional() -> None:
    period = resolve_period(competence="2026-10", start_date=None, end_date=None)
    assert period.competence == "2026-10"
    assert period.start_date == "01-10-2026"
    assert period.end_date == "31-10-2026"


def test_resolve_period_blank_dates_equal_absent() -> None:
    """Contrato: string vazia/blank é ausência semântica, não malformada.

    resolve_period_dates (api-delpi) e normalize_dashboard_period_date (SI)
    definem "" como ausente — parâmetro blank equivale ao omitido.
    """
    blank = resolve_period(competence="2026-10", start_date="", end_date="  ")
    omitted = resolve_period(competence="2026-10", start_date=None, end_date=None)
    assert blank == omitted


def _app() -> FastAPI:
    app = FastAPI()
    app.include_router(goals_router)
    return app


def _main_app() -> FastAPI:
    app = FastAPI()
    app.include_router(main_router)
    return app


def _as_viewer():
    return set_current_user(
        SimpleNamespace(
            id="user-1",
            is_superadmin=False,
            permissions=["strategic-indicators.view"],
            rbac_unavailable=False,
        )
    )


def _use_case_running_resolve_period():
    """Stub do use case que executa o resolve_period real (camada validada)."""
    use_case = MagicMock()

    def _execute(**kwargs):
        resolve_period(
            competence=kwargs["competence"],
            start_date=kwargs["start_date"],
            end_date=kwargs["end_date"],
        )
        return []

    use_case.execute.side_effect = _execute
    return use_case


def test_dashboard_goals_route_returns_400_for_malformed_start_date() -> None:
    with patch(
        "si_app.interface.http.routes.integrations_routes."
        "build_get_dashboard_goals_by_source_keys_use_case",
        return_value=_use_case_running_resolve_period(),
    ):
        response = TestClient(_app()).get(
            "/strategic-indicators/integrations/dashboard-goals",
            params={"source_keys": "quality.ppm", "start_date": "01-10-202"},
        )
    assert response.status_code == 400
    assert "inválida" in response.json()["detail"]


def test_dashboard_goals_route_preserves_valid_date_success() -> None:
    with patch(
        "si_app.interface.http.routes.integrations_routes."
        "build_get_dashboard_goals_by_source_keys_use_case",
        return_value=_use_case_running_resolve_period(),
    ):
        response = TestClient(_app()).get(
            "/strategic-indicators/integrations/dashboard-goals",
            params={
                "source_keys": "quality.ppm",
                "start_date": "01-10-2026",
                "end_date": "31-10-2026",
            },
        )
    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_dashboard_goals_route_blank_dates_equal_omitted() -> None:
    with patch(
        "si_app.interface.http.routes.integrations_routes."
        "build_get_dashboard_goals_by_source_keys_use_case",
        return_value=_use_case_running_resolve_period(),
    ):
        blank = TestClient(_app()).get(
            "/strategic-indicators/integrations/dashboard-goals",
            params={"source_keys": "quality.ppm", "start_date": "", "end_date": ""},
        )
        omitted = TestClient(_app()).get(
            "/strategic-indicators/integrations/dashboard-goals",
            params={"source_keys": "quality.ppm"},
        )
    assert blank.status_code == omitted.status_code == 200
    assert blank.json() == omitted.json() == {"items": []}


def test_departments_read_route_returns_400_for_malformed_start_date() -> None:
    """Cobre run_logged_read_route + except HTTPException: raise nas rotas de leitura."""
    use_case = MagicMock()

    def _execute(request):
        resolve_period(
            competence=request.competence,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        return {"items": []}

    use_case.execute.side_effect = _execute
    token = _as_viewer()
    try:
        with patch(
            "si_app.interface.http.routes.strategic_indicators_routes."
            "build_get_strategic_indicators_departments_use_case",
            return_value=use_case,
        ):
            response = TestClient(_main_app()).get(
                "/strategic-indicators/departments",
                params={"start_date": "01-10-202"},
            )
            valid_response = TestClient(_main_app()).get(
                "/strategic-indicators/departments",
                params={"start_date": "01-10-2026", "end_date": "31-10-2026"},
            )
    finally:
        reset_current_user(token)

    assert response.status_code == 400
    assert "inválida" in response.json()["detail"]
    assert valid_response.status_code == 200
