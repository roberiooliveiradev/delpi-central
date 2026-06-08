"""Exemplos OpenAPI (códigos fictícios — prefixos PA/PI/MP)."""

PRODUCT_STOCK_EXAMPLE = {
    "success": True,
    "message": "Estoque do produto carregado com sucesso.",
    "data": {
        "items": [
            {
                "product_code": "90269001",
                "branch": "01",
                "warehouse": "01",
                "available_quantity": 105.0,
            }
        ],
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1,
    },
    "error": None,
    "meta": {
        "dataVersion": "2026-06",
        "operationId": "get_product_stock",
        "entity": "product_stock",
        "shape": "paged_list",
        "pagination": {"page": 1, "page_size": 50, "total": 1, "total_pages": 1},
        "fields": {
            "available_quantity": "Saldo disponível (atual - empenhado - reservado)",
        },
    },
}

PRODUCT_STRUCTURE_EXAMPLE = {
    "success": True,
    "message": "Estrutura do produto carregada com sucesso.",
    "data": {
        "root": {
            "code": "90269001",
            "description": "PRODUTO FICTICIO PA",
            "type": "PA",
            "quantity": 1.0,
        },
        "items": [
            {
                "code": "50219001",
                "description": "INTERMEDIARIO FICTICIO",
                "type": "PI",
                "components": [
                    {
                        "code": "10019001",
                        "description": "MATERIA-PRIMA FICTICIA",
                        "type": "MP",
                        "components": [],
                    }
                ],
            }
        ],
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1,
    },
    "error": None,
    "meta": {
        "dataVersion": "2026-06",
        "operationId": "get_product_structure",
        "entity": "product_structure",
        "shape": "hierarchy",
    },
}

PRODUCT_FACTORY_STATUS_EXAMPLE = {
    "success": True,
    "message": "Status fabril completo do produto carregado com sucesso.",
    "data": {
        "product": {"product_code": "90269002", "description": "PRODUTO FICTICIO FABRIL"},
        "factory_status": "OP ABERTA / NÃO INICIADO",
        "structure": {"items": [], "summary": {"total_components": 0}},
        "production": {"items": [], "summary": {}},
        "shipping": {"items": [], "summary": {}},
    },
    "error": None,
    "meta": {
        "dataVersion": "2026-06",
        "operationId": "get_product_factory_status",
        "entity": "product_factory_status",
        "shape": "composite_analysis",
    },
}

PRODUCT_DETAIL_EXAMPLE = {
    "success": True,
    "message": "Operação realizada com sucesso",
    "data": {
        "product": {
            "code": "90269001",
            "description": "PRODUTO FICTICIO PA",
            "type": "PA",
            "unit": "UN",
            "group_code": "9026",
            "sale_price": 125.5,
            "default_warehouse": "01",
            "revision": "001",
            "ncm": "00000000",
        }
    },
    "error": None,
    "meta": {
        "dataVersion": "2026-06",
        "operationId": "get_product_detail",
        "entity": "product",
        "shape": "product_snapshot",
    },
}

PRODUCT_SEARCH_EXAMPLE = {
    "success": True,
    "message": "Operação realizada com sucesso",
    "data": {
        "items": [{"code": "90269001", "description": "PRODUTO FICTICIO PA", "type": "PA"}],
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1,
    },
    "error": None,
    "meta": {
        "dataVersion": "2026-06",
        "operationId": "search_products",
        "entity": "product_search",
        "shape": "paged_list",
    },
}

PRODUCT_SUMMARY_EXAMPLE = {
    "success": True,
    "message": "Resumo do produto carregado com sucesso.",
    "data": {
        "product": {"code": "90269001", "description": "PRODUTO FICTICIO PA"},
        "stock": [],
        "prices": [],
    },
    "error": None,
    "meta": {
        "dataVersion": "2026-06",
        "operationId": "get_product_summary",
        "entity": "product",
        "shape": "product_snapshot",
    },
}

PRODUCT_ANALYSER_EXAMPLE = {
    "success": True,
    "message": "Analisador do produto carregado com sucesso.",
    "data": {
        "product": {"code": "90269001", "description": "PRODUTO FICTICIO PA"},
        "structure": {"items": [], "total": 0},
        "guide": {"items": [], "total": 0},
        "inspection": {"items": [], "total": 0},
    },
    "error": None,
    "meta": {
        "dataVersion": "2026-06",
        "operationId": "get_product_analyser",
        "entity": "product_analyser",
        "shape": "composite_analysis",
    },
}
