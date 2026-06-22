"""Sprint 4 — programação do dia com códigos auditáveis na tabela e no texto."""

from __future__ import annotations

from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import (
    load_api_delpi_data,
    load_api_delpi_fixture_with_meta,
)


def test_production_schedule_today_table_preserves_product_codes() -> None:
    presenter = ExternalActionResultPresenter()
    data = load_api_delpi_data("production_schedule_today_20260622.json")

    table = presenter._playbook_report()._build_playbook_report_table(
        data,
        "/production/schedule/today",
        entity="production_schedule_today",
    )

    assert table is not None
    rows = table.get("rows") or []
    codes = {
        str(row.get("product_code") or "").strip()
        for row in rows
        if isinstance(row, dict)
    }

    assert "90260140" in codes
    assert "90261255" in codes


def test_production_schedule_today_text_lists_codes_with_descriptions() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("production_schedule_today_20260622.json")
    result = presenter.present(envelope, path="/production/schedule/today")
    joined = "\n".join(str(line) for line in result.get("linhas") or [])

    assert "90260140" in joined
    assert "90261255" in joined
    assert "PA HOMOLOGADO REF" in joined
