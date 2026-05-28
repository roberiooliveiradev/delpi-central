"""Casos de regressão — Onda 6 (perguntas reais da operação)."""

from app.domain.services.chat_product_query_intent_service import ChatProductQueryIntent

INTENT_CASES = [
    ("descrição do produto 10080047", ChatProductQueryIntent.DESCRIPTION),
    ("qual a descrição do 10.080.055", ChatProductQueryIntent.DESCRIPTION),
    ("busque o estoque desse produto", ChatProductQueryIntent.STOCK),
    ("saldo disponível do item", ChatProductQueryIntent.STOCK),
    ("informações completas do produto 10080055", ChatProductQueryIntent.DESCRIPTION),
    ("qual o valor total de estoque da empresa", ChatProductQueryIntent.FULL),
    ("explique o procedimento de estoque e política interna", ChatProductQueryIntent.FULL),
]

PRODUCT_CODE_CASES = [
    ("produto 10.080.055", "10080055"),
    ("código 10080047", "10080047"),
    ("detalhe da LMP da OV 123456", None),
    (
        "estoque desse produto",
        "10080047",
        "assistant: Produto 10080047: TERM. PINO RETO",
    ),
    (
        "o que mais pode me dizer sobre um produto?",
        "10070088",
        "assistant: Produto 10070088: CABO PP CIRCULAR",
    ),
    (
        "mais informações sobre o item",
        "10080047",
        "assistant: Produto 10080047: TERM. PINO RETO",
    ),
    (
        "estoque do produto",
        "10080055",
        "assistant: Produto 10080047: A\nassistant: Produto 10080055: B",
    ),
]

ANALYSIS_INTENT_CASES = [
    ("compare as duas estruturas e traga insights", True),
    ("quais as diferenças entre os produtos?", True),
    ("estrutura do produto 90260088", False),
]

MISSING_PRODUCT_CODE_CASES = [
    ("estoque do produto", True),
    ("estouque do produto", True),
    ("estoque do produto 10080099", False),
    ("qual o valor total de estoque da empresa", False),
]

OPERATIONAL_FAST_PATH_CASES = [
    ("estoque do produto 10080047", True),
    ("descrição do produto 10080047", True),
    (
        (
            "explique o procedimento completo de como consultar estoque "
            "e saldo disponível nas filiais segundo a política interna"
        ),
        False,
    ),
    ("olá, tudo bem?", False),
]

SELECTION_CASES = [
    {
        "message": "estoque do produto 10080047",
        "actions": [
            {
                "actionId": "stock",
                "method": "GET",
                "path": "/products/{code}/stock",
                "operationId": "get_product_stock",
                "summary": "Estoque do produto",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "analyser",
                "method": "GET",
                "path": "/products/{code}/analyser",
                "operationId": "get_product_analyser",
                "summary": "Analisador",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "stock",
    },
    {
        "message": "qual o valor total de estoque",
        "actions": [
            {
                "actionId": "product-stock",
                "method": "GET",
                "path": "/products/{code}/stock",
                "operationId": "get_product_stock",
                "summary": "Estoque produto",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "supplies-stock",
                "method": "GET",
                "path": "/supplies/stock-value",
                "operationId": "get_supplies_stock_value",
                "summary": "Valor total estoque",
                "parametersSchema": [],
            },
        ],
        "expected_action_id": "supplies-stock",
    },
    {
        "message": "detalhe da LMP da OV 123456",
        "actions": [
            {
                "actionId": "list-lmps",
                "method": "GET",
                "path": "/engineering/lmps",
                "operationId": "list_lmps",
                "summary": "Listar LMPs",
                "parametersSchema": [],
            },
            {
                "actionId": "get-lmp",
                "method": "GET",
                "path": "/engineering/lmps/{sale_number}",
                "operationId": "get_lmp_by_sale_number",
                "summary": "LMP por OV",
                "parametersSchema": [{"name": "sale_number"}],
            },
        ],
        "expected_action_id": "get-lmp",
    },
    {
        "message": "qual o CPV da filial 01 no último mês",
        "actions": [
            {
                "actionId": "cpv",
                "method": "GET",
                "path": "/supplies/cpv",
                "operationId": "get_supplies_cpv",
                "summary": "CPV suprimentos",
                "parametersSchema": [{"name": "branch"}],
            },
            {
                "actionId": "stock-value",
                "method": "GET",
                "path": "/supplies/stock-value",
                "operationId": "get_supplies_stock_value",
                "summary": "Valor total estoque",
                "parametersSchema": [],
            },
        ],
        "expected_action_id": "cpv",
    },
    {
        "message": "mostre o OTD de compras",
        "actions": [
            {
                "actionId": "otd",
                "method": "GET",
                "path": "/supplies/otd",
                "operationId": "get_supplies_otd",
                "summary": "OTD suprimentos",
                "parametersSchema": [],
            },
            {
                "actionId": "cpv",
                "method": "GET",
                "path": "/supplies/cpv",
                "operationId": "get_supplies_cpv",
                "summary": "CPV",
                "parametersSchema": [],
            },
        ],
        "expected_action_id": "otd",
    },
    {
        "message": "histórico de compras do produto 10080047",
        "actions": [
            {
                "actionId": "purchases",
                "method": "GET",
                "path": "/products/{code}/purchases",
                "operationId": "get_product_purchases",
                "summary": "Compras do produto",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "analyser",
                "method": "GET",
                "path": "/products/{code}/analyser",
                "operationId": "get_product_analyser",
                "summary": "Analisador",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "purchases",
    },
    {
        "message": "qual o giro de estoque da filial 01",
        "actions": [
            {
                "actionId": "inventory",
                "method": "GET",
                "path": "/supplies/inventory-turnover",
                "operationId": "get_supplies_inventory_turnover",
                "summary": "Giro de estoque",
                "parametersSchema": [{"name": "branch"}],
            },
            {
                "actionId": "stock-value",
                "method": "GET",
                "path": "/supplies/stock-value",
                "operationId": "get_supplies_stock_value",
                "summary": "Valor total estoque",
                "parametersSchema": [],
            },
        ],
        "expected_action_id": "inventory",
    },
    {
        "message": "dashboard de LMPs em aberto",
        "actions": [
            {
                "actionId": "lmp-dash",
                "method": "GET",
                "path": "/engineering/lmps/dashboard",
                "operationId": "list_lmps_dashboard",
                "summary": "Dashboard LMPs",
                "parametersSchema": [],
            },
            {
                "actionId": "list-lmps",
                "method": "GET",
                "path": "/engineering/lmps",
                "operationId": "list_lmps",
                "summary": "Listar LMPs",
                "parametersSchema": [],
            },
        ],
        "expected_action_id": "lmp-dash",
    },
    {
        "message": "resumo de vendas do produto 10080047",
        "actions": [
            {
                "actionId": "sales-summary",
                "method": "GET",
                "path": "/products/{code}/sales",
                "operationId": "get_product_sales_summary",
                "summary": "Vendas do produto",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "purchases",
                "method": "GET",
                "path": "/products/{code}/purchases",
                "operationId": "get_product_purchases",
                "summary": "Compras",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "sales-summary",
    },
    {
        "message": "carteira de pedidos em aberto do produto 10080047",
        "actions": [
            {
                "actionId": "open-orders",
                "method": "GET",
                "path": "/products/{code}/sales/open-orders",
                "operationId": "get_product_sales_open_orders",
                "summary": "Carteira do produto",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "sales-summary",
                "method": "GET",
                "path": "/products/{code}/sales",
                "operationId": "get_product_sales_summary",
                "summary": "Vendas",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "open-orders",
    },
    {
        "message": "listar ordens de venda da semana",
        "actions": [
            {
                "actionId": "sale-orders",
                "method": "GET",
                "path": "/sales/",
                "operationId": "list_sale_orders",
                "summary": "Ordens de venda",
                "parametersSchema": [{"name": "date_start"}],
            },
            {
                "actionId": "list-lmps",
                "method": "GET",
                "path": "/engineering/lmps",
                "operationId": "list_lmps",
                "summary": "LMPs",
                "parametersSchema": [],
            },
        ],
        "expected_action_id": "sale-orders",
    },
    {
        "message": "busque 3 produtos do grupo 1008",
        "actions": [
            {
                "actionId": "search",
                "method": "GET",
                "path": "/products/search",
                "operationId": "search_products",
                "summary": "Busca de produtos",
                "parametersSchema": [
                    {"name": "group_code"},
                    {"name": "page_size"},
                ],
            },
            {
                "actionId": "analyser",
                "method": "GET",
                "path": "/products/{code}/analyser",
                "operationId": "get_product_analyser",
                "summary": "Analisador",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "search",
        "expected_parameters": {"group_code": "1008"},
    },
    {
        "message": "liste produtos do grupo MP",
        "actions": [
            {
                "actionId": "search",
                "method": "GET",
                "path": "/products/search",
                "operationId": "search_products",
                "summary": "Busca de produtos",
                "parametersSchema": [
                    {"name": "description"},
                    {"name": "group_code"},
                    {"name": "page_size"},
                ],
            },
        ],
        "expected_action_id": "search",
        "expected_parameters": {"group_code": "MP"},
    },
    {
        "message": "qual o ebitda do último trimestre",
        "actions": [
            {
                "actionId": "ebitda",
                "method": "GET",
                "path": "/financial/ebitda_pct",
                "operationId": "get_ebitda_pct",
                "summary": "EBITDA",
                "parametersSchema": [],
            },
            {
                "actionId": "rol-fin",
                "method": "GET",
                "path": "/financial/rol",
                "operationId": "get_rol",
                "summary": "ROL",
                "parametersSchema": [],
            },
        ],
        "expected_action_id": "ebitda",
    },
    {
        "message": "taxa de conversão de vendas",
        "actions": [
            {
                "actionId": "closing",
                "method": "GET",
                "path": "/commercial/closing-rate",
                "operationId": "get_sales_conversion_rate",
                "summary": "Taxa de conversão",
                "parametersSchema": [],
            },
        ],
        "expected_action_id": "closing",
    },
    {
        "message": "resumo de kaizens do mês",
        "actions": [
            {
                "actionId": "kaizen",
                "method": "GET",
                "path": "/quality/kaizens/summary",
                "operationId": "get_kaizen_summary",
                "summary": "Kaizens",
                "parametersSchema": [],
            },
        ],
        "expected_action_id": "kaizen",
    },
    {
        "message": "oee da produção",
        "actions": [
            {
                "actionId": "oee",
                "method": "GET",
                "path": "/production/overall_equipment_effectiveness_pct",
                "operationId": "get_overall_equipment_effectiveness_pct",
                "summary": "OEE",
                "parametersSchema": [],
            },
        ],
        "expected_action_id": "oee",
    },
    {
        "message": "resumo do produto 10080047",
        "actions": [
            {
                "actionId": "summary",
                "method": "GET",
                "path": "/products/{code}/summary",
                "operationId": "get_product_summary",
                "summary": "Resumo do produto",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "analyser",
                "method": "GET",
                "path": "/products/{code}/analyser",
                "operationId": "get_product_analyser",
                "summary": "Analisador",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "summary",
    },
    {
        "message": "ficha completa do produto 10080047",
        "actions": [
            {
                "actionId": "summary",
                "method": "GET",
                "path": "/products/{code}/summary",
                "operationId": "get_product_summary",
                "summary": "Resumo",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "analyser",
                "method": "GET",
                "path": "/products/{code}/analyser",
                "operationId": "get_product_analyser",
                "summary": "Analisador completo",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "analyser",
    },
    {
        "message": "faturamento do produto 10080047",
        "actions": [
            {
                "actionId": "billing",
                "method": "GET",
                "path": "/products/{code}/sales/billing",
                "operationId": "get_product_sales_billing",
                "summary": "Faturamento",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "sales-summary",
                "method": "GET",
                "path": "/products/{code}/sales",
                "operationId": "get_product_sales_summary",
                "summary": "Vendas",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "billing",
    },
    {
        "message": "kpis do painel de LMPs",
        "actions": [
            {
                "actionId": "dash-summary",
                "method": "GET",
                "path": "/engineering/lmps/dashboard/summary",
                "operationId": "get_lmps_dashboard_summary",
                "summary": "KPIs painel LMP",
                "parametersSchema": [],
            },
            {
                "actionId": "lmp-dash",
                "method": "GET",
                "path": "/engineering/lmps/dashboard",
                "operationId": "list_lmps_dashboard",
                "summary": "Dashboard LMPs",
                "parametersSchema": [],
            },
        ],
        "expected_action_id": "dash-summary",
    },
    {
        "message": "processos do transforma mais",
        "actions": [
            {
                "actionId": "tm-processes",
                "method": "GET",
                "path": "/engineering/transforma-mais/processes",
                "operationId": "list_transforma_mais_processes",
                "summary": "Processos Transforma Mais",
                "parametersSchema": [],
            },
            {
                "actionId": "tm-summary",
                "method": "GET",
                "path": "/engineering/transforma-mais/processes/summary",
                "operationId": "get_transforma_mais_summary",
                "summary": "Resumo Transforma Mais",
                "parametersSchema": [],
            },
        ],
        "expected_action_id": "tm-processes",
    },
    {
        "message": "colunas da tabela SB1",
        "actions": [
            {
                "actionId": "table-columns",
                "method": "GET",
                "path": "/system/tables/{tableName}/columns",
                "operationId": "list_table_columns",
                "summary": "Colunas da tabela",
                "parametersSchema": [{"name": "tableName"}],
            },
            {
                "actionId": "tables-search",
                "method": "GET",
                "path": "/system/tables/search",
                "operationId": "search_tables",
                "summary": "Buscar tabelas",
                "parametersSchema": [{"name": "description"}],
            },
        ],
        "expected_action_id": "table-columns",
        "expected_parameters": {"tableName": "SB1"},
    },
    {
        "message": "pmr da filial 02",
        "actions": [
            {
                "actionId": "pmr",
                "method": "GET",
                "path": "/financial/pmr",
                "operationId": "get_pmr",
                "summary": "PMR",
                "parametersSchema": [{"name": "branch"}],
            },
        ],
        "expected_action_id": "pmr",
        "expected_parameters": {"branch": "02"},
    },
]

DIRECT_ANSWER_CASES = [
    {
        "humanized": {
            "titulo": "Lista de LMPs",
            "linhas": [
                "OV 123 · LMP · Aberto: AMOSTRA CLIENTE X",
                "Total: 2 registro(s) (página 1).",
            ],
        },
        "path": "/engineering/lmps",
        "operation_id": "list_lmps",
        "message": "listar lmps",
        "must_contain": ["**Lista de LMPs**", "OV 123"],
    },
    {
        "humanized": {
            "titulo": "Consulta SQL",
            "linhas": [
                "A consulta retornou 2 registro(s).",
                "1. code=10080047, description=PARAFUSO",
            ],
        },
        "path": "/data/sql",
        "operation_id": "execute_readonly_sql",
        "message": "select top 2",
        "must_contain": ["**Consulta SQL**", "2 registro"],
    },
    {
        "humanized": {
            "titulo": "CPV",
            "linhas": [
                "Filial 01 · CPV: 12,5%",
                "Top 3 itens listados.",
            ],
        },
        "path": "/supplies/cpv",
        "operation_id": "get_supplies_cpv",
        "message": "qual o cpv",
        "must_contain": ["**CPV", "Filial 01"],
    },
    {
        "humanized": {
            "titulo": "Detalhe LMP OV 123456",
            "linhas": [
                "OV 123456 · LMP · Status: Aberto",
                "Cliente: ACME",
            ],
        },
        "path": "/engineering/lmps/123456",
        "operation_id": "get_lmp_by_sale_number",
        "message": "detalhe lmp ov 123456",
        "must_contain": ["**Detalhe", "OV 123456"],
    },
]

_STOCK_CONVERSATION_HISTORY = [
    {"role": "user", "content": "estoque do produto 10080022"},
    {
        "role": "assistant",
        "content": "Estoque do produto 10080022",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "ok": True,
                        "path": "/products/10080022/stock",
                        "actionId": "stock",
                    },
                }
            ]
        },
    },
]

STOCK_REFINEMENT_SELECTION_CASES = [
    {
        "message": "filtre filial 02",
        "previous_messages": _STOCK_CONVERSATION_HISTORY,
        "actions": [
            {
                "actionId": "stock",
                "method": "GET",
                "path": "/products/{code}/stock",
                "operationId": "get_product_stock",
                "summary": "Estoque do produto",
                "parametersSchema": [
                    {"name": "code", "in": "path", "required": True},
                    {"name": "branch", "in": "query"},
                ],
            },
            {
                "actionId": "analyser",
                "method": "GET",
                "path": "/products/{code}/analyser",
                "operationId": "get_product_analyser",
                "summary": "Analisador",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "stock",
        "expected_parameters": {"code": "10080022", "branch": "02"},
    },
]

OPERATIONAL_REFINEMENT_FAST_PATH_CASES = [
    ("filtre filial 02", True, _STOCK_CONVERSATION_HISTORY),
    ("filtre filial 02", False, []),
]

AGENTIC_SKIP_REFINEMENT_CASES = [
    ("filtre filial 02", True, _STOCK_CONVERSATION_HISTORY),
    ("filtre filial 02", False, []),
]
