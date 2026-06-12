from unittest.mock import MagicMock

import pytest

from maint_app.infrastructure.persistence.repositories.filial_repository import (
    FilialRepository,
    normalize_codigo_filial,
)


def test_normalize_codigo_filial_accepts_two_digits():
    assert normalize_codigo_filial("01") == "01"
    assert normalize_codigo_filial(" 02 ") == "02"


def test_normalize_codigo_filial_rejects_invalid():
    with pytest.raises(ValueError):
        normalize_codigo_filial("1")
    with pytest.raises(ValueError):
        normalize_codigo_filial("abc")


def test_create_rejects_duplicate():
    conn = MagicMock()
    repo = FilialRepository(connection=conn)
    repo.get = MagicMock(return_value={"filial_id": 1, "codigo_filial": "01"})
    with pytest.raises(ValueError, match="já existe"):
        repo.create({"codigo_filial": "01", "nome_filial": "Matriz"})


def test_soft_delete_rejects_operational_links():
    conn = MagicMock()
    repo = FilialRepository(connection=conn)
    repo.get = MagicMock(return_value={"filial_id": 1, "codigo_filial": "01"})
    repo.count_operational_links = MagicMock(return_value=3)
    with pytest.raises(ValueError, match="dados operacionais"):
        repo.soft_delete("01")
