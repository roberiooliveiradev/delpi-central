from unittest.mock import MagicMock

from app.application.dto.mini_applicators.list_ferramentas_request import (
    ListMiniApplicatorsFerramentasRequest,
)
from app.application.models.page import Page
from app.application.use_cases.mini_applicators.mini_applicators_use_cases import (
    ListMiniApplicatorsFerramentasUseCase,
)
from app.domain.entities.mini_applicators.mini_applicator_tool import MiniApplicatorTool


def test_list_mini_applicators_ferramentas_use_case():
    mock_repo = MagicMock()
    mock_repo.list_ferramentas.return_value = Page(
        items=[
            MiniApplicatorTool(id=1, codigo="23-001", descricao="Teste", grupo="23"),
        ],
        total=1,
        page=1,
        page_size=50,
    )

    use_case = ListMiniApplicatorsFerramentasUseCase(mock_repo)
    result = use_case.execute(ListMiniApplicatorsFerramentasRequest(descricao="23-"))

    assert result.total == 1
    assert result.items[0].codigo == "23-001"
    mock_repo.list_ferramentas.assert_called_once()


def test_list_mini_applicators_componentes_use_case():
    mock_repo = MagicMock()
    mock_repo.list_componentes.return_value = [
        {
            "id": 1,
            "nivel": 1,
            "codigo": "3019-001",
            "descricao": "Peça teste",
            "unidade": "UN",
            "estoque_local_01": 10.0,
            "estoque_local_99": 0.0,
        }
    ]

    from app.application.use_cases.mini_applicators.mini_applicators_use_cases import (
        ListMiniApplicatorsComponentesUseCase,
    )

    use_case = ListMiniApplicatorsComponentesUseCase(mock_repo)
    result = use_case.execute(codigo_ferramenta="23-001", filial="01")

    assert len(result) == 1
    assert result[0]["codigo"] == "3019-001"
    mock_repo.list_componentes.assert_called_once_with(codigo_ferramenta="23-001", filial="01")
