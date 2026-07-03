from unittest.mock import MagicMock

from maint_app.infrastructure.gateways.delpi_mini_applicators_gateway import (
    DelpiMiniAplicatorsGateway,
)


def test_listar_ferramentas_propaga_client(monkeypatch):
    client = MagicMock()
    client.list_mini_applicators_ferramentas.return_value = {
        "total": 1,
        "items": [{"id": 1, "codigo": "23-001", "descricao": "Teste"}],
    }
    monkeypatch.setattr(
        "maint_app.infrastructure.gateways.delpi_mini_applicators_gateway.bearer_authorization_from_context",
        lambda: "Bearer token",
    )

    gateway = DelpiMiniAplicatorsGateway(client)
    result = gateway.listar_ferramentas(descricao="23-", filial="01", page=1, page_size=20)

    assert result["total"] == 1
    client.list_mini_applicators_ferramentas.assert_called_once_with(
        params={
            "codigo": None,
            "descricao": "23-",
            "filial": "01",
            "page": "1",
            "page_size": "20",
            "sort_by": None,
            "sort_dir": None,
            "incluir_bloqueados": None,
            "codigo_peca": None,
            "descricao_peca": None,
        },
        authorization="Bearer token",
    )


def test_obter_ferramenta_propaga_client(monkeypatch):
    client = MagicMock()
    client.get_mini_applicators_ferramenta.return_value = {
        "id": 1,
        "codigo": "23-026",
        "descricao": "Mini aplicador",
    }
    monkeypatch.setattr(
        "maint_app.infrastructure.gateways.delpi_mini_applicators_gateway.bearer_authorization_from_context",
        lambda: "Bearer token",
    )

    gateway = DelpiMiniAplicatorsGateway(client)
    result = gateway.obter_ferramenta("23-026")

    assert result["codigo"] == "23-026"
    client.get_mini_applicators_ferramenta.assert_called_once_with(
        "23-026",
        authorization="Bearer token",
    )


def test_listar_componentes_propaga_client(monkeypatch):
    client = MagicMock()
    client.list_mini_applicators_componentes.return_value = {
        "items": [{"codigo": "3019-001", "nivel": 1}],
        "total": 1,
    }
    monkeypatch.setattr(
        "maint_app.infrastructure.gateways.delpi_mini_applicators_gateway.bearer_authorization_from_context",
        lambda: "Bearer token",
    )

    gateway = DelpiMiniAplicatorsGateway(client)
    result = gateway.listar_componentes(codigo_ferramenta="23-026", filial="01")

    assert result["total"] == 1
    client.list_mini_applicators_componentes.assert_called_once_with(
        "23-026",
        params={"filial": "01"},
        authorization="Bearer token",
    )


def test_listar_pecas_reposicao_propaga_client(monkeypatch):
    client = MagicMock()
    client.list_mini_applicators_pecas_reposicao.return_value = {
        "items": [{"codigo": "30190036", "descricao": "FACA DE CORTE"}],
        "total": 1,
    }
    monkeypatch.setattr(
        "maint_app.infrastructure.gateways.delpi_mini_applicators_gateway.bearer_authorization_from_context",
        lambda: "Bearer token",
    )

    gateway = DelpiMiniAplicatorsGateway(client)
    result = gateway.listar_pecas_reposicao(codigo="3019", page=1, page_size=20)

    assert result["total"] == 1
    client.list_mini_applicators_pecas_reposicao.assert_called_once_with(
        params={
            "codigo": "3019",
            "descricao": None,
            "page": "1",
            "page_size": "20",
            "sort_by": None,
            "sort_dir": None,
        },
        authorization="Bearer token",
    )


def test_listar_onde_usado_propaga_client(monkeypatch):
    client = MagicMock()
    client.get_product_parents.return_value = {
        "items": [{"code": "90260142", "description": "PA teste", "quantity": 1, "parents": []}],
        "total": 1,
    }
    monkeypatch.setattr(
        "maint_app.infrastructure.gateways.delpi_mini_applicators_gateway.bearer_authorization_from_context",
        lambda: "Bearer token",
    )

    gateway = DelpiMiniAplicatorsGateway(client)
    result = gateway.listar_onde_usado(codigo_ferramenta="23-026")

    assert result["total"] == 1
    client.get_product_parents.assert_called_once_with(
        "23-026",
        authorization="Bearer token",
    )
