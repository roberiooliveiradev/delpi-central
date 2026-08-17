"""normalize_favorite_items — validação de favoritos do hub."""

from __future__ import annotations

import pytest

from commercial_app.infrastructure.persistence.repositories.postgres_home_favorites_repository import (
    normalize_favorite_items,
)


def test_normalize_accepts_valid_items():
    items = normalize_favorite_items(
        [{"viewId": "proposals"}, {"viewId": "my_tasks", "search": "bucket=overdue"}]
    )
    assert items == [
        {"viewId": "proposals"},
        {"viewId": "my_tasks", "search": "?bucket=overdue"},
    ]


def test_normalize_rejects_unknown_view():
    with pytest.raises(ValueError, match="invalid viewId"):
        normalize_favorite_items([{"viewId": "not_a_view"}])


def test_normalize_dedupes():
    items = normalize_favorite_items(
        [
            {"viewId": "proposals"},
            {"viewId": "proposals"},
        ]
    )
    assert len(items) == 1
