from unittest.mock import patch

from app.infrastructure.persistence.totvs.engineering_repositories.mini_applicators_repository import (
    MiniApplicatorsRepository,
)


def test_list_pecas_deriva_da_arvore_vigente_de_componentes():
    repo = MiniApplicatorsRepository()
    componentes = [
        {"codigo": "10080006", "descricao": "TERM FASTON", "nivel": 1},
        {"codigo": "30190825", "descricao": "GRAMPEADOR ISOLANTE", "nivel": 1},
        {"codigo": "30190036", "descricao": "FACA DE CORTE", "nivel": 1},
    ]

    with patch.object(repo, "list_componentes", return_value=componentes) as list_componentes:
        pecas = repo.list_pecas("23-001", filial="01")

    list_componentes.assert_called_once_with(codigo_ferramenta="23-001", filial="01")
    assert [item["codigo"] for item in pecas] == ["30190036", "30190825"]
    assert all(item["grupo"] == "3019" for item in pecas)
