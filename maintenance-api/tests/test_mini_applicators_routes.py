from maint_app.interface.http.routes.mini_applicators_routes import _filter_pecas_reposicao


def test_filter_pecas_reposicao_mantem_somente_3019():
    items = [
        {"codigo": "30190026", "descricao": "FACA"},
        {"codigo": "10080006", "descricao": "TERM FASTON"},
        {"codigo": "30194313", "descricao": "GRAMPO"},
    ]

    filtered = _filter_pecas_reposicao(items)

    assert [item["codigo"] for item in filtered] == ["30190026", "30194313"]


def test_filter_pecas_reposicao_preserva_ordem_da_estrutura():
    items = [
        {"codigo": "30190825", "descricao": "GRAMPEADOR ISOLANTE", "nivel": 1},
        {"codigo": "30190036", "descricao": "FACA DE CORTE", "nivel": 1},
    ]

    filtered = _filter_pecas_reposicao(items)

    assert [item["codigo"] for item in filtered] == ["30190825", "30190036"]
