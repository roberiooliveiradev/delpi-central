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
