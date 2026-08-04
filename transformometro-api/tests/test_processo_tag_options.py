import pytest

from tm_app.infrastructure.persistence.repositories.processo_repository import (
    ProcessoRepository,
)


def test_list_distinct_tag_values_rejects_unknown_column():
    repo = ProcessoRepository.__new__(ProcessoRepository)
    with pytest.raises(ValueError, match="coluna inválida"):
        repo.list_distinct_tag_values("nome_processo")
