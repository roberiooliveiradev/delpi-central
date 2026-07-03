from maint_app.interface.http.routes.mini_applicators_routes import (
    _filter_pecas_reposicao,
    _flatten_parents,
    _sort_onde_usado,
)


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


def test_flatten_parents_expande_hierarquia():
    items = [
        {
            "code": "90260142",
            "description": "PA nivel 1",
            "type": "PA",
            "unit": "PC",
            "quantity": 1,
            "parents": [
                {
                    "code": "10080006",
                    "description": "PA nivel 2",
                    "type": "PI",
                    "unit": "PC",
                    "quantity": 2,
                    "parents": [],
                }
            ],
        }
    ]

    rows = _flatten_parents(items)

    assert len(rows) == 2
    assert rows[0]["nivel"] == 1
    assert rows[0]["codigo"] == "90260142"
    assert rows[1]["nivel"] == 2
    assert rows[1]["codigo"] == "10080006"


def test_sort_onde_usado_por_codigo():
    items = [
        {"nivel": 1, "codigo": "B", "descricao": "", "tipo": "", "unidade": "", "quantidade": 1},
        {"nivel": 1, "codigo": "A", "descricao": "", "tipo": "", "unidade": "", "quantidade": 1},
    ]

    sorted_items = _sort_onde_usado(items, "codigo", "asc")

    assert [item["codigo"] for item in sorted_items] == ["A", "B"]
