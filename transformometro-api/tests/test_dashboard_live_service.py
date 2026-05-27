from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from tm_app.application.services.dashboard_live_service import DashboardLiveService
from tm_app.domain.raw_data import TransformometroRawData

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> TransformometroRawData:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return TransformometroRawData(**payload)


@patch("tm_app.application.services.dashboard_live_service.DashboardDataRepository")
def test_build_summary_marks_live_source(mock_repo):
    raw = _load_fixture("golden_baseline_melhoria.json")
    mock_repo.return_value.load_raw.return_value = raw

    summary = DashboardLiveService().build_summary()

    assert summary["fonte"] == "cadastro_tempo_real"
    assert "economia_liquida_total" in summary
    assert isinstance(summary.get("evolucao_mensal"), list)
