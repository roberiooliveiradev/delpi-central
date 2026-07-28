from __future__ import annotations

from tv_app.infrastructure.persistence.repositories.playlist_repository import (
    MainSectionProtectedError,
    _row_to_section,
)


def test_row_to_section_exposes_is_main():
    row = {
        "id": "11111111-1111-1111-1111-111111111111",
        "playlist_id": "22222222-2222-2222-2222-222222222222",
        "name": "Principal",
        "sort_order": 0,
        "is_collapsed": False,
        "is_active": True,
        "is_main": True,
        "default_duration_sec": None,
        "transition_style": None,
        "master_config": {},
        "created_at": None,
        "updated_at": None,
    }
    section = _row_to_section(row)
    assert section["isMain"] is True
    assert section["name"] == "Principal"


def test_row_to_section_is_main_defaults_false():
    row = {
        "id": "11111111-1111-1111-1111-111111111111",
        "playlist_id": "22222222-2222-2222-2222-222222222222",
        "name": "Seção 1",
        "sort_order": 1,
        "is_collapsed": False,
        "is_active": True,
        "master_config": {},
        "created_at": None,
        "updated_at": None,
    }
    section = _row_to_section(row)
    assert section["isMain"] is False


def test_main_section_protected_error_is_value_error():
    err = MainSectionProtectedError()
    assert isinstance(err, ValueError)
