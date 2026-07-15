from __future__ import annotations

from unittest.mock import MagicMock

from app.application.use_cases.kaizen.import_kaizens_from_sheet_use_case import (
    ImportKaizensFromSheetUseCase,
)
from app.domain.entities.kaizen.kaizen import KaizenDetail
from app.domain.services.kaizen.kaizen_sheet_import_mapper import (
    normalize_sheet_status,
    sheet_detail_to_record_fields,
)


def test_normalize_sheet_status_maps_implantado() -> None:
    assert normalize_sheet_status("Implantado") == "implantado"
    assert normalize_sheet_status("em andamento") == "recebido"


def test_sheet_detail_to_record_fields_maps_time_inputs() -> None:
    fields = sheet_detail_to_record_fields(
        KaizenDetail(
            id="01-16/01/2026-App resina CT-16",
            title="App resina CT-16",
            date_implemented="16/01/2026",
            status="implantado",
            accountable="Ossamu",
            sector="Produção",
            investment=620.0,
            daily_savings=7.54,
            annual_savings=2752.1,
            branch="01",
            seconds_per_occurrence=1015.96,
            occurrences_per_day=0.21,
            hourly_cost=127.16,
            hours_saved_per_day=0.0593,
        )
    )
    assert fields["branch_code"] == "01"
    assert fields["date_implemented"] == "2026-01-16"
    assert fields["seconds_per_occurrence"] == 1015.96
    assert fields["status"] == "implantado"


def test_import_use_case_skips_existing_and_creates_new() -> None:
    sheet_source = MagicMock()
    sheet_source.list_active_kaizen_details.return_value = [
        KaizenDetail(
            id="01-16/01/2026-App resina CT-16",
            title="App resina CT-16",
            date_implemented="16/01/2026",
            status="implantado",
            accountable=None,
            sector=None,
            investment=None,
            daily_savings=7.54,
            annual_savings=2752.1,
            branch="01",
            seconds_per_occurrence=1015.96,
            occurrences_per_day=0.21,
            hourly_cost=127.16,
        ),
        KaizenDetail(
            id="01-07/01/2026-Novo",
            title="Novo kaizen",
            date_implemented="07/01/2026",
            status="recebido",
            accountable=None,
            sector=None,
            investment=None,
            daily_savings=None,
            annual_savings=None,
            branch="01",
        ),
    ]

    record_repository = MagicMock()
    record_repository.list_records.side_effect = [
        {"items": [{"date_implemented": "2026-01-16"}]},
        {"items": []},
    ]
    record_repository.create_record.return_value = {
        "id": "new-id",
        "title": "Novo kaizen",
        "daily_savings": None,
    }

    result = ImportKaizensFromSheetUseCase(sheet_source, record_repository).execute(
        created_by_user_id="user-1",
    )

    assert result.created == 1
    assert result.skipped == 1
    assert result.errors == 0
    record_repository.create_record.assert_called_once()
