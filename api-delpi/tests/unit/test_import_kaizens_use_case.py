from __future__ import annotations

from unittest.mock import MagicMock

from app.application.use_cases.kaizen.import_kaizens_use_case import ImportKaizensUseCase


def test_import_skips_existing_and_invalid_branch_and_creates_new() -> None:
    repo = MagicMock()
    repo.list_records.side_effect = [
        {"items": [{"date_implemented": "2026-01-16"}]},  # já existe
        {"items": []},  # novo
    ]
    repo.create_record.return_value = {"id": "new-id", "daily_savings": 5.0}

    items = [
        {"branch_code": "01", "title": "Existe", "date_implemented": "2026-01-16"},
        {"branch_code": "01", "title": "Novo"},
        {"branch_code": "99", "title": "Filial inválida"},
        {"branch_code": "01", "title": ""},
    ]

    result = ImportKaizensUseCase(repo).execute(items, created_by_user_id="user-1")

    assert result.created == 1
    assert result.skipped == 3
    assert result.errors == 0
    repo.create_record.assert_called_once()


def test_import_dry_run_does_not_create() -> None:
    repo = MagicMock()
    repo.list_records.return_value = {"items": []}

    result = ImportKaizensUseCase(repo).execute(
        [{"branch_code": "02", "title": "Simulado"}],
        created_by_user_id="user-1",
        dry_run=True,
    )

    assert result.created == 1
    repo.create_record.assert_not_called()


def test_import_reports_error_per_item_without_aborting() -> None:
    repo = MagicMock()
    repo.list_records.return_value = {"items": []}
    repo.create_record.side_effect = [RuntimeError("boom"), {"id": "ok"}]

    result = ImportKaizensUseCase(repo).execute(
        [
            {"branch_code": "01", "title": "Falha"},
            {"branch_code": "01", "title": "Sucesso"},
        ],
        created_by_user_id="user-1",
        skip_existing=False,
    )

    assert result.created == 1
    assert result.errors == 1
