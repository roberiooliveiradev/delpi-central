"""Casos de regressão — Onda 6 (perguntas reais da operação)."""

from app.domain.services.chat_product_query_intent_service import ChatProductQueryIntent

DRAWING_INTENT_CASES = [
    ("analise o desenho 90260140", True),
    ("validar pdf do desenho tecnico 90264130", True),
    ("gerar relatorio tecnico do desenho 90260140", True),
    ("gerar relatorio de conformidade delpi 90260140", True),
    ("emitir relatorio de conformidade do desenho 90264130", True),
    ("auditar desenho tecnico 90260140", True),
    ("validar conformidade do desenho 90260140", True),
    ("comparar pdf com protheus 90260140", True),
    ("liberar desenho para producao 90260140", True),
    ("conferir bom do pdf anexado", True),
    ("validar carimbo do desenho em pdf", True),
    ("estoque do produto 10080047", False),
    ("informacoes completas do produto 10080055", False),
    ("qual a descricao do produto 10080047", False),
]

INTENT_CASES = [
    ("analise o desenho 90260140", ChatProductQueryIntent.ANALYSER),
    ("validar pdf do desenho tecnico 90264130", ChatProductQueryIntent.ANALYSER),
    ("descrição do produto 10080047", ChatProductQueryIntent.DESCRIPTION),
    ("qual a descrição do 10.080.055", ChatProductQueryIntent.DESCRIPTION),
    ("busque o estoque desse produto", ChatProductQueryIntent.STOCK),
    ("saldo disponível do item", ChatProductQueryIntent.STOCK),
    ("informações completas do produto 10080055", ChatProductQueryIntent.ANALYSER),
    (
        "análise integrada do cadastro, roteiro e estrutura do 90260149",
        ChatProductQueryIntent.ANALYSER,
    ),
    (
        "estrutura e roteiro do produto 90260149",
        ChatProductQueryIntent.MULTI_SCOPE,
    ),
    (
        "roteiro e inspeção do produto 90260149",
        ChatProductQueryIntent.MULTI_SCOPE,
    ),
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
        "message": "mostre vendas do produto 10080001",
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
                "actionId": "stock-wrong",
                "method": "GET",
                "path": "/products/{code}/stock",
                "operationId": "stock_products_code_stock_get",
                "summary": "Estoque",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "sales-summary",
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
        "message": "Qual a taxa de conversão de vendas da empresa?",
        "actions": [
            {
                "actionId": "product-sales",
                "method": "GET",
                "path": "/products/{code}/sales",
                "operationId": "get_product_sales_summary",
                "summary": "Vendas do produto",
                "parametersSchema": [{"name": "code"}],
            },
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
        "message": "Qual o OTD de compras da empresa?",
        "actions": [
            {
                "actionId": "commercial-otd",
                "method": "GET",
                "path": "/commercial/sales-order-otd",
                "operationId": "get_sales_order_otd",
                "summary": "OTD comercial",
                "parametersSchema": [],
            },
            {
                "actionId": "supplies-otd",
                "method": "GET",
                "path": "/supplies/otd",
                "operationId": "get_supplies_otd",
                "summary": "OTD suprimentos",
                "parametersSchema": [],
            },
        ],
        "expected_action_id": "supplies-otd",
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
        "message": "Quanto já foi faturado do produto 90260015?",
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
        "message": "Qual o status completo na fábrica do produto 90269002 hoje?",
        "actions": [
            {
                "actionId": "factory-status",
                "method": "GET",
                "path": "/products/{code}/factory-status",
                "operationId": "get_product_factory_status",
                "summary": "Status fabril",
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
        "expected_action_id": "factory-status",
    },
    {
        "message": "O produto 90269002 já começou a produzir? Tem apontamento na OP?",
        "actions": [
            {
                "actionId": "production-status",
                "method": "GET",
                "path": "/products/{code}/production-status",
                "operationId": "get_product_production_status",
                "summary": "Análise produtiva",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "factory-status",
                "method": "GET",
                "path": "/products/{code}/factory-status",
                "operationId": "get_product_factory_status",
                "summary": "Status fabril",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "production-status",
    },
    {
        "message": "Quanto do produto 90269002 já foi liberado para expedição hoje?",
        "actions": [
            {
                "actionId": "shipping-status",
                "method": "GET",
                "path": "/products/{code}/shipping-status",
                "operationId": "get_product_shipping_status",
                "summary": "Expedição do PA",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "inspection",
                "method": "GET",
                "path": "/products/{code}/inspection",
                "operationId": "get_product_inspection",
                "summary": "Inspeção de qualidade",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "factory-status",
                "method": "GET",
                "path": "/products/{code}/factory-status",
                "operationId": "get_product_factory_status",
                "summary": "Status fabril",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "shipping-status",
    },
    {
        "message": "Quais matérias-primas exclusivas existem na estrutura do produto 90269002?",
        "actions": [
            {
                "actionId": "structure-exclusivity",
                "method": "GET",
                "path": "/products/{code}/structure/exclusivity",
                "operationId": "get_product_structure_exclusivity",
                "summary": "Estrutura com exclusividade",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "structure",
                "method": "GET",
                "path": "/products/{code}/structure",
                "operationId": "get_product_structure",
                "summary": "Estrutura do produto",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "structure-exclusivity",
    },
    {
        "message": "Quais matérias-primas são exclusivas?",
        "actions": [
            {
                "actionId": "exclusive-raw-materials-catalog",
                "method": "GET",
                "path": "/products/exclusive-raw-materials/catalog",
                "operationId": "list_exclusive_raw_materials_catalog",
                "summary": "Catálogo global de MPs exclusivas",
                "parametersSchema": [
                    {"name": "view"},
                    {"name": "limit"},
                ],
            },
            {
                "actionId": "structure-exclusivity",
                "method": "GET",
                "path": "/products/{code}/structure/exclusivity",
                "operationId": "get_product_structure_exclusivity",
                "summary": "Estrutura com exclusividade",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "exclusive-raw-materials-catalog",
    },
    {
        "message": "Quais produtos têm matéria-prima exclusiva?",
        "actions": [
            {
                "actionId": "exclusive-raw-materials-catalog",
                "method": "GET",
                "path": "/products/exclusive-raw-materials/catalog",
                "operationId": "list_exclusive_raw_materials_catalog",
                "summary": "Catálogo global de MPs exclusivas",
                "parametersSchema": [
                    {"name": "view"},
                    {"name": "limit"},
                ],
            },
        ],
        "expected_action_id": "exclusive-raw-materials-catalog",
    },
    {
        "message": "Quais itens mais consumidos no mês?",
        "actions": [
            {
                "actionId": "production-consumption-top-items",
                "method": "GET",
                "path": "/production/consumption/top-items",
                "operationId": "get_production_consumption_top_items",
                "summary": "Itens mais consumidos na produção",
                "parametersSchema": [
                    {"name": "date_start"},
                    {"name": "date_end"},
                    {"name": "limit"},
                ],
            },
        ],
        "expected_action_id": "production-consumption-top-items",
    },
    {
        "message": "Produtos mais comprados em março",
        "actions": [
            {
                "actionId": "purchases-top-products",
                "method": "GET",
                "path": "/purchases/top-products",
                "operationId": "get_purchases_top_products",
                "summary": "Produtos mais comprados no período",
                "parametersSchema": [
                    {"name": "date_start"},
                    {"name": "date_end"},
                    {"name": "limit"},
                ],
            },
        ],
        "expected_action_id": "purchases-top-products",
    },
    {
        "message": "Quais produtos estão programados para produzir hoje?",
        "actions": [
            {
                "actionId": "production-schedule-today",
                "method": "GET",
                "path": "/production/schedule/today",
                "operationId": "get_production_schedule_today",
                "summary": "Produtos programados para produzir na data",
                "parametersSchema": [
                    {"name": "reference_date"},
                    {"name": "limit"},
                ],
            },
        ],
        "expected_action_id": "production-schedule-today",
    },
    {
        "message": "Análise de preço da matéria-prima 10080001",
        "actions": [
            {
                "actionId": "raw-material-price-intelligence",
                "method": "GET",
                "path": "/products/{code}/raw-material-price-intelligence",
                "operationId": "get_product_raw_material_price_intelligence",
                "summary": "Análise inteligente de preço de matéria-prima",
                "parametersSchema": [
                    {"name": "code"},
                    {"name": "date_start"},
                    {"name": "date_end"},
                ],
            },
            {
                "actionId": "pricing",
                "method": "GET",
                "path": "/products/{code}/pricing",
                "operationId": "get_product_pricing",
                "summary": "Preços do produto",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "purchases",
                "method": "GET",
                "path": "/products/{code}/purchases",
                "operationId": "get_product_purchases",
                "summary": "Compras do produto",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "raw-material-price-intelligence",
    },
    {
        "message": "Última compra e ICMS do produto 10080001",
        "actions": [
            {
                "actionId": "last-purchase",
                "method": "GET",
                "path": "/products/{code}/last-purchase",
                "operationId": "get_product_last_purchase",
                "summary": "Última compra válida da matéria-prima",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "raw-material-price-intelligence",
                "method": "GET",
                "path": "/products/{code}/raw-material-price-intelligence",
                "operationId": "get_product_raw_material_price_intelligence",
                "summary": "Análise inteligente de preço de matéria-prima",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "purchases",
                "method": "GET",
                "path": "/products/{code}/purchases",
                "operationId": "get_product_purchases",
                "summary": "Compras do produto",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "last-purchase",
    },
    {
        "message": "Histórico de orçamento de compra do produto 10080001",
        "actions": [
            {
                "actionId": "purchase-budget-history",
                "method": "GET",
                "path": "/products/{code}/purchase-budget-history",
                "operationId": "get_product_purchase_budget_history",
                "summary": "Histórico de orçamento de compra",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "purchases",
                "method": "GET",
                "path": "/products/{code}/purchases",
                "operationId": "get_product_purchases",
                "summary": "Compras do produto",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "purchase-budget-history",
    },
    {
        "message": "Quais materiais mais impactam o custo do PA 90261255?",
        "actions": [
            {
                "actionId": "cost-impact-simulation",
                "method": "GET",
                "path": "/products/{code}/cost-impact-simulation",
                "operationId": "get_product_cost_impact_simulation",
                "summary": "Simulador de impacto de custos do PA",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "structure",
                "method": "GET",
                "path": "/products/{code}/structure",
                "operationId": "get_product_structure",
                "summary": "Estrutura do produto",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "cost-impact-simulation",
    },
    {
        "message": "Simule aumento de 10% nos materiais do produto 90261255",
        "actions": [
            {
                "actionId": "cost-impact-simulation",
                "method": "GET",
                "path": "/products/{code}/cost-impact-simulation",
                "operationId": "get_product_cost_impact_simulation",
                "summary": "Simulador de impacto de custos do PA",
                "parametersSchema": [
                    {"name": "code"},
                    {"name": "adjustment_percent"},
                ],
            },
            {
                "actionId": "pricing",
                "method": "GET",
                "path": "/products/{code}/pricing",
                "operationId": "get_product_pricing",
                "summary": "Preços do produto",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "cost-impact-simulation",
        "expected_parameters": {"adjustment_percent": 10.0},
    },
    {
        "message": "Qual o preço de venda do produto 10080001?",
        "actions": [
            {
                "actionId": "pricing",
                "method": "GET",
                "path": "/products/{code}/pricing",
                "operationId": "get_product_pricing",
                "summary": "Preços do produto",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "raw-material-price-intelligence",
                "method": "GET",
                "path": "/products/{code}/raw-material-price-intelligence",
                "operationId": "get_product_raw_material_price_intelligence",
                "summary": "Análise inteligente de preço de matéria-prima",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "pricing",
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
        "message": "qual a tabela de produtos?",
        "actions": [
            {
                "actionId": "tables-search",
                "method": "GET",
                "path": "/system/tables/search",
                "operationId": "search_tables",
                "summary": "Buscar tabelas",
                "parametersSchema": [{"name": "description"}],
            },
            {
                "actionId": "product-search",
                "method": "GET",
                "path": "/products/search",
                "operationId": "search_products",
                "summary": "Buscar produtos",
                "parametersSchema": [{"name": "description"}],
            },
        ],
        "expected_action_id": "tables-search",
        "expected_parameters": {"description": "produtos"},
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
    {
        "message": "roteiro do produto 90260142",
        "actions": [
            {
                "actionId": "guide",
                "method": "GET",
                "path": "/products/{code}/guide",
                "operationId": "guide_products_code_guide_get",
                "summary": "Roteiro de produção",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "structure",
                "method": "GET",
                "path": "/products/{code}/structure",
                "operationId": "get_product_structure",
                "summary": "Estrutura",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "guide",
        "expected_parameters": {"code": "90260142"},
    },
    {
        "message": "inspeção do produto 90260142",
        "actions": [
            {
                "actionId": "inspection",
                "method": "GET",
                "path": "/products/{code}/inspection",
                "operationId": "list_product_inspection",
                "summary": "Plano de inspeção",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "guide",
                "method": "GET",
                "path": "/products/{code}/guide",
                "operationId": "guide_products_code_guide_get",
                "summary": "Roteiro",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "inspection",
        "expected_parameters": {"code": "90260142"},
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

PRESENTER_HUMANIZED_CASES = [
    {
        "label": "fornecedores_vazio",
        "payload": {
            "success": True,
            "message": "Fornecedores de 10090077 retornados com sucesso (página 1/0).",
            "data": {
                "success": True,
                "total": 0,
                "page": 1,
                "page_size": 50,
                "total_pages": 0,
                "data": [],
            },
        },
        "path": "/products/10090077/suppliers",
        "must_contain": ["10090077", "Nenhum fornecedor"],
    },
    {
        "label": "roteiro",
        "payload": {
            "items": [
                {
                    "branch": "01",
                    "product_code": "90260142",
                    "operation_code": "01",
                    "operation_description": "CORTAR - MANUAL",
                    "work_center": "CT-05",
                    "bom_level": 0,
                },
                {
                    "branch": "01",
                    "product_code": "90260142",
                    "operation_code": "02",
                    "operation_description": "INSERIR TUBO ISOLANTE",
                    "work_center": "CT-08",
                    "bom_level": 0,
                },
                {
                    "branch": "01",
                    "product_code": "50230070",
                    "operation_code": "01",
                    "operation_description": "CORTAR / DECAPAR - MAQUINA",
                    "work_center": "CT-01A",
                    "bom_level": 1,
                },
            ]
        },
        "path": "/products/90260142/guide",
        "must_contain": ["90260142", "CORTAR - MANUAL", "componente"],
    },
    {
        "label": "estoque",
        "payload": {
            "items": [
                {
                    "branch": "01",
                    "warehouse": "01",
                    "current_quantity": 100,
                    "available_quantity": 80,
                    "committed_quantity": 20,
                    "physical_location": "A-01",
                },
                {
                    "branch": "02",
                    "warehouse": "01",
                    "current_quantity": 50,
                    "available_quantity": 50,
                    "committed_quantity": 0,
                    "physical_location": "B-02",
                },
            ]
        },
        "path": "/products/10080055/stock",
        "must_contain": ["10080055", "disponível", "Filial"],
    },
    {
        "label": "estrutura",
        "payload": {
            "root": {
                "code": "90260142",
                "description": "CABO TESTE",
                "type": "PA",
                "unit": "UN",
                "quantity": 1,
            },
            "items": [
                {
                    "code": "50230070",
                    "description": "TERMINAL A",
                    "type": "ME",
                    "unit": "UN",
                    "quantity": 2,
                },
                {
                    "code": "10030015",
                    "description": "FIO COBRE",
                    "type": "MP",
                    "unit": "M",
                    "quantity": 1.5,
                },
            ],
            "total": 2,
        },
        "path": "/products/90260142/structure",
        "must_contain": ["90260142", "50230070", "matéria"],
    },
    {
        "label": "inspeção aninhada",
        "payload": {
            "items": [
                {
                    "product_code": "90260142",
                    "bom_level": 0,
                    "has_inspection": True,
                    "header": {"description": "Plano principal"},
                    "measurable_tests": [{"test_code": "T01", "sequence": 1}],
                    "textual_tests": [{"test_code": "T02", "sequence": 2}],
                }
            ]
        },
        "path": "/products/90260142/inspection",
        "must_contain": ["90260142", "Plano principal", "dimensional"],
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

_PARENTS_CONVERSATION_HISTORY = [
    {"role": "user", "content": "onde é usado o 10080022"},
    {
        "role": "assistant",
        "content": "Produtos pai (onde é usado)",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "arguments": {
                        "actionId": "parents",
                        "parameters": {
                            "code": "10080022",
                            "page": 1,
                            "page_size": 25,
                        },
                    },
                    "metadata": {
                        "ok": True,
                        "path": "/products/10080022/parents",
                        "actionId": "parents",
                        "dataCoverageNotice": {
                            "kind": "pagination",
                            "message": "Produtos pai parcial: página 1 de 3.",
                        },
                    },
                }
            ]
        },
    },
]

_GUIDE_CONVERSATION_HISTORY = [
    {"role": "user", "content": "roteiro do 90260142"},
    {
        "role": "assistant",
        "content": "Roteiro do produto",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "ok": True,
                        "path": "/products/90260142/guide",
                        "actionId": "guide_products_code_guide_get",
                    },
                }
            ]
        },
    },
]

_SQL_RESULT_HISTORY = [
    {
        "role": "assistant",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {"ok": True, "path": "/data/sql"},
                }
            ]
        },
    }
]

DATA_INTERPRETATION_CASES = [
    ("interprete o resultado da última consulta SQL", _SQL_RESULT_HISTORY, True),
    ("explique os dados acima", _GUIDE_CONVERSATION_HISTORY, True),
    ("o que isso quer dizer", _GUIDE_CONVERSATION_HISTORY, True),
    ("resume", _STOCK_CONVERSATION_HISTORY, True),
    ("traduz isso", _GUIDE_CONVERSATION_HISTORY, True),
    ("nao entendi", _STOCK_CONVERSATION_HISTORY, True),
    ("roteiro do 90260142", None, False),
    ("explique os dados acima", None, False),
]

DATA_INTERPRETATION_SKIP_TOOLS_CASES = [
    ("explique os dados acima", _GUIDE_CONVERSATION_HISTORY, True),
    ("resume", _STOCK_CONVERSATION_HISTORY, True),
    ("traduz isso", _GUIDE_CONVERSATION_HISTORY, True),
    ("estoque do produto 10080047", None, False),
]

DATA_INTERPRETATION_NO_ACTION_CASES = [
    {
        "message": "explique os dados acima",
        "previous_messages": _GUIDE_CONVERSATION_HISTORY,
        "actions": [
            {
                "actionId": "sql",
                "method": "POST",
                "path": "/data/sql",
                "operationId": "execute_readonly_sql",
                "summary": "Executar SQL",
                "parametersSchema": [],
            },
            {
                "actionId": "guide",
                "method": "GET",
                "path": "/products/{code}/guide",
                "operationId": "guide_products_code_guide_get",
                "summary": "Roteiro",
                "parametersSchema": [{"name": "code"}],
            },
        ],
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
    {
        "message": "filtre filial 02",
        "previous_messages": [
            {"role": "user", "content": "estoque do produto 10080022"},
            {
                "role": "assistant",
                "content": "Estoque do produto 10080022",
                "metadata": {
                    "toolCalls": [
                        {
                            "name": "execute_external_action",
                            "arguments": {
                                "actionId": "stock",
                                "parameters": {
                                    "code": "10080022",
                                    "page": 1,
                                    "page_size": 50,
                                },
                            },
                            "metadata": {
                                "ok": True,
                                "path": "/products/{code}/stock",
                                "actionId": "stock",
                            },
                        }
                    ]
                },
            },
        ],
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
        ],
        "expected_action_id": "stock",
        "expected_parameters": {"code": "10080022", "branch": "02"},
    },
]

_STOCK_VALUE_HISTORY = [
    {"role": "user", "content": "qual o valor total de estoque da empresa"},
    {
        "role": "assistant",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {"ok": True, "path": "/supplies/stock-value"},
                }
            ]
        },
    },
]

OPERATIONAL_REFINEMENT_FAST_PATH_CASES = [
    ("filtre filial 02", True, _STOCK_CONVERSATION_HISTORY),
    ("filtre filial 02", False, []),
    ("filial 01", True, _STOCK_VALUE_HISTORY),
    ("filial 01", False, []),
    ("aumente para 50 linhas", True, _PARENTS_CONVERSATION_HISTORY),
    ("aumente para 50 linhas", False, []),
    ("proxima pagina", True, _PARENTS_CONVERSATION_HISTORY),
    ("proxima pagina", False, []),
]

AGENTIC_SKIP_REFINEMENT_CASES = [
    ("filtre filial 02", True, _STOCK_CONVERSATION_HISTORY),
    ("filtre filial 02", False, []),
    ("filial 01", True, _STOCK_VALUE_HISTORY),
    ("filial 01", False, []),
    ("aumente para 50 linhas", True, _PARENTS_CONVERSATION_HISTORY),
    ("aumente para 50 linhas", False, []),
    ("proxima pagina", True, _PARENTS_CONVERSATION_HISTORY),
    ("proxima pagina", False, []),
]

PAGINATION_REFINEMENT_SELECTION_CASES = [
    {
        "message": "aumente para 50 linhas",
        "previous_messages": _PARENTS_CONVERSATION_HISTORY,
        "actions": [
            {
                "actionId": "parents",
                "method": "GET",
                "path": "/products/{code}/parents",
                "operationId": "get_product_parents",
                "summary": "Produtos pai",
                "parametersSchema": [
                    {"name": "code", "in": "path", "required": True},
                    {"name": "page", "in": "query"},
                    {"name": "page_size", "in": "query"},
                ],
            },
        ],
        "expected_action_id": "parents",
        "expected_parameters": {"code": "10080022", "page": 1, "page_size": 50},
    },
    {
        "message": "proxima pagina",
        "previous_messages": _PARENTS_CONVERSATION_HISTORY,
        "actions": [
            {
                "actionId": "parents",
                "method": "GET",
                "path": "/products/{code}/parents",
                "operationId": "get_product_parents",
                "summary": "Produtos pai",
                "parametersSchema": [
                    {"name": "code", "in": "path", "required": True},
                    {"name": "page", "in": "query"},
                    {"name": "page_size", "in": "query"},
                ],
            },
        ],
        "expected_action_id": "parents",
        "expected_parameters": {"code": "10080022", "page": 2, "page_size": 25},
    },
    {
        "message": "proxima pagina",
        "previous_messages": [
            {"role": "user", "content": "onde é usado o 10080022"},
            {"role": "assistant", "content": "Produtos pai", "metadata": {}},
        ],
        "actions": [
            {
                "actionId": "parents",
                "method": "GET",
                "path": "/products/{code}/parents",
                "operationId": "get_product_parents",
                "summary": "Produtos pai",
                "parametersSchema": [
                    {"name": "code", "in": "path", "required": True},
                    {"name": "page", "in": "query"},
                    {"name": "page_size", "in": "query"},
                ],
            },
        ],
        "expected_action_id": "parents",
        "expected_parameters": {"code": "10080022", "page": 2, "page_size": 25},
    },
]

DATE_RANGE_SELECTION_CASES = [
    {
        "message": "status fabril do produto 90269002 essa semana",
        "actions": [
            {
                "actionId": "factory-status",
                "method": "GET",
                "path": "/products/{code}/factory-status",
                "operationId": "get_product_factory_status",
                "summary": "Status fabril",
                "parametersSchema": [
                    {"name": "code"},
                    {"name": "reference_date"},
                    {"name": "date_start"},
                    {"name": "date_end"},
                ],
            },
        ],
        "expected_action_id": "factory-status",
        "expected_parameters": {
            "code": "90269002",
            "reference_date": "08-06-2026",
            "date_start": "08-06-2026",
            "date_end": "14-06-2026",
        },
    },
    {
        "message": "status fabril do produto 90269002 hoje",
        "actions": [
            {
                "actionId": "factory-status",
                "method": "GET",
                "path": "/products/{code}/factory-status",
                "operationId": "get_product_factory_status",
                "summary": "Status fabril",
                "parametersSchema": [
                    {"name": "code"},
                    {"name": "reference_date"},
                ],
            },
            {
                "actionId": "stock",
                "method": "GET",
                "path": "/products/{code}/stock",
                "operationId": "get_product_stock",
                "summary": "Estoque",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "factory-status",
        "expected_parameters": {
            "code": "90269002",
        },
    },
    {
        "message": "status fabril do produto 90263059 em 01/06/2026",
        "actions": [
            {
                "actionId": "factory-status",
                "method": "GET",
                "path": "/products/{code}/factory-status",
                "operationId": "get_product_factory_status",
                "summary": "Status fabril",
                "parametersSchema": [
                    {"name": "code"},
                    {"name": "reference_date"},
                    {"name": "date_start"},
                    {"name": "date_end"},
                ],
            },
        ],
        "expected_action_id": "factory-status",
        "expected_parameters": {
            "code": "90263059",
            "reference_date": "01-06-2026",
            "date_start": "01-06-2026",
            "date_end": "01-06-2026",
        },
    },
    {
        "message": "cpv de 01/04/2026 a 30/04/2026",
        "actions": [
            {
                "actionId": "supplies-cpv",
                "method": "GET",
                "path": "/supplies/cpv",
                "operationId": "get_supplies_cpv",
                "summary": "CPV suprimentos",
                "parametersSchema": [
                    {"name": "start_date", "in": "query"},
                    {"name": "end_date", "in": "query"},
                    {"name": "branch", "in": "query"},
                ],
            },
        ],
        "expected_action_id": "supplies-cpv",
        "expected_parameters": {
            "start_date": "01-04-2026",
            "end_date": "30-04-2026",
        },
    },
    {
        "message": "listar ov de 01/04/2026 a 30/04/2026",
        "actions": [
            {
                "actionId": "sales-list",
                "method": "GET",
                "path": "/sales",
                "operationId": "list_sale_orders",
                "summary": "Ordens de venda",
                "parametersSchema": [
                    {"name": "date_start", "in": "query"},
                    {"name": "date_end", "in": "query"},
                    {"name": "page", "in": "query"},
                    {"name": "page_size", "in": "query"},
                ],
            },
        ],
        "expected_action_id": "sales-list",
        "expected_parameters": {
            "date_start": "01-04-2026",
            "date_end": "30-04-2026",
            "page": 1,
            "page_size": 50,
        },
    },
]

_SUMMARY_HISTORY = [
    {"role": "user", "content": "resumo do produto 10080047"},
    {
        "role": "assistant",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "ok": True,
                        "path": "/products/10080047/summary",
                    },
                }
            ]
        },
    },
]

MULTI_TURN_PRODUCT_CODE_CASES = [
    (
        "ultimas compras",
        "10080047",
        _SUMMARY_HISTORY,
    ),
    (
        "estoque do produto",
        "10080055",
        [
            {"role": "assistant", "content": "Produto 10080047: A"},
            {"role": "assistant", "content": "Produto 10080055: B"},
        ],
    ),
]

MULTI_TURN_INTENT_CASES = [
    (
        "ultimas compras",
        ChatProductQueryIntent.FULL,
        _SUMMARY_HISTORY,
    ),
    (
        "estoque do produto",
        ChatProductQueryIntent.STOCK,
        _STOCK_CONVERSATION_HISTORY,
    ),
]

METRIC_REFINEMENT_SELECTION_CASES = [
    {
        "message": "filtre filial 02",
        "previous_messages": [
            {"role": "user", "content": "qual o cpv"},
            {
                "role": "assistant",
                "metadata": {
                    "toolCalls": [
                        {
                            "name": "execute_external_action",
                            "metadata": {"ok": True, "path": "/supplies/cpv"},
                        }
                    ]
                },
            },
        ],
        "actions": [
            {
                "actionId": "supplies-cpv",
                "method": "GET",
                "path": "/supplies/cpv",
                "operationId": "get_supplies_cpv",
                "summary": "CPV",
                "parametersSchema": [
                    {"name": "start_date"},
                    {"name": "end_date"},
                    {"name": "branch"},
                ],
            },
        ],
        "expected_action_id": "supplies-cpv",
        "expected_parameters": {"branch": "02"},
    },
    {
        "message": "filial 01",
        "previous_messages": _STOCK_VALUE_HISTORY,
        "actions": [
            {
                "actionId": "stock-value",
                "method": "GET",
                "path": "/supplies/stock-value",
                "operationId": "get_supplies_stock_value",
                "summary": "Valor total estoque",
                "parametersSchema": [
                    {"name": "branch"},
                    {"name": "top_limit"},
                ],
            },
        ],
        "expected_action_id": "stock-value",
        "expected_parameters": {"branch": "01"},
    },
]

EMAIL_WRITING_SUBTYPE_CASES = [
    ("escreva um e-mail formal para Robério sobre IA no Minha DELPI", "email_create"),
    ("redija um e-mail para o fornecedor sobre prazo", "email_create"),
    ("deixe o e-mail anterior mais curto", "email_shorten"),
    ("deixe o e-mail anterior mais formal", "email_formalize"),
    ("tom mais firme no e-mail anterior", "email_firm"),
    ("crie 3 opções de assunto para o e-mail", "email_subjects"),
    ("traduza o e-mail anterior para inglês", "email_translate"),
    ("responda este e-mail de forma educada", "email_reply"),
]

EMAIL_PURE_TEXT_TASK_CASES = [
    ("escreva um e-mail formal para a diretoria", True),
    ("corrija: segue documento em anexo", True),
    ("consulte estoque do 10080001 e escreva um e-mail", False),
    ("escreva um email com os dados da tabela", True),
]

EMAIL_WRITING_MODE_CASES = [
    ("escreva um e-mail para compras", True),
    ("qual o estoque do produto 10080001", False),
]

EMAIL_PREFERENCE_DETECT_CASES = [
    ("daqui pra frente sempre faça e-mails curtos", {"shortEmails": True}),
    ("sempre use tom formal nos e-mails", {"formalTone": True}),
    ("sempre deixe assinatura em branco nos e-mails", {"blankSignature": True}),
]

TEXT_CORRECTION_SUBTYPE_CASES = [
    ("corrija: o estoque esta baixo", "text_correct_basic"),
    ("corrija e explique: nos vai enviar o pedido", "text_correct_explain"),
    ("corrija e mostre antes e depois deste texto", "text_correct_compare"),
    ("corrija sem mudar meu estilo: segue os arquivo", "text_correct_preserve_style"),
    ("deixe mais formal: preciso que envie isso", "text_correct_formal"),
    ("reescreva de forma mais profissional este parágrafo", "text_correct_professional"),
    ("reescreva mantendo o sentido deste trecho", "text_rewrite"),
]

TEXT_CORRECTION_MODE_CASES = [
    ("corrija: o estoque esta baixo", True),
    ("consulte estoque do 10080001", False),
    ("corrija este e-mail: texto solto", False),
]

TEXT_CORRECTION_PURE_TEXT_TASK_CASES = [
    ("corrija: segue em anexo os documento", True),
    ("consulte produto e corrija o texto depois", False),
]

TEXT_CORRECTION_PREFERENCE_DETECT_CASES = [
    (
        "daqui pra frente entregue só a versão final quando pedir correção",
        {"deliverFinalOnly": True},
    ),
    ("sempre mostre antes e depois ao corrigir texto", {"showBeforeAfter": True}),
]

TEXT_CORRECTION_SOURCE_CASES = [
    ("corrija o texto da lousa", "canvas"),
    ("revise o texto do anexo pdf", "attachment"),
    ("corrija: o estoque esta baixo", "user_message"),
]

SESSION_MEMORY_REFERENCE_CASES = [
    ("agora fornecedores", {"productCode": "10080001"}, ["productCode"]),
    ("mesmo período", {"period": "last_30_days"}, ["period"]),
    ("esse produto", {"productCode": "10080001"}, ["productCode"]),
]

SESSION_MEMORY_CLEAR_CASES = [
    ("limpe o contexto", True),
    ("começar do zero", True),
    ("esqueça esse produto", False),
]

SESSION_MEMORY_BEHAVIOR_CASES = [
    ("daqui pra frente responda curto", {"answerLength": "short"}),
    ("use tom formal", {"tone": "formal"}),
    ("sempre em tabela", {"responseFormat": "table"}),
]

CONTEXT_ASSERTIVENESS_CASES = [
    {
        "message": "Quem fornece o produto 10080001?",
        "tool_paths": ["/products/10080001/analyser"],
        "expected_flags": ["supplier_intent_used_analyser"],
        "max_score": 70.0,
    },
    {
        "message": "agora estoque",
        "tool_paths": ["/products/10080001/stock"],
        "snapshot": {
            "followUpDetected": True,
            "operationalFocus": {"productCode": "10080001"},
        },
        "expected_flags": ["follow_up_entity_reused"],
        "min_score": 80.0,
    },
    {
        "message": "agora fornecedores",
        "tool_paths": [],
        "snapshot": {
            "followUpDetected": True,
            "operationalFocus": {"productCode": "10080001"},
        },
        "expected_flags": ["follow_up_without_entity_reuse"],
        "max_score": 65.0,
    },
    {
        "message": "me fale do produto 10080001",
        "answer": "Informe o código do produto para consultar.",
        "tool_paths": [],
        "snapshot": {
            "followUpDetected": False,
            "operationalFocus": {"productCode": "10080001"},
        },
        "expected_flags": ["unnecessary_code_request"],
        "max_score": 75.0,
    },
    {
        "message": "me fale do produto 10080001",
        "answer": "Produto **None**: None.",
        "tool_paths": ["/products/10080001/analyser"],
        "snapshot": {"operationalFocus": {"productCode": "10080001"}},
        "expected_flags": ["humanized_none_fields"],
        "max_score": 60.0,
    },
]


# Gate de turno simples (Playbook de Inteligência, seções 4-8).
# (mensagem, intent_esperado_ou_None). None = não deve ser turno simples (mostra etapas).
SIMPLE_TURN_GATE_CASES = [
    ("ola", "small_talk"),
    ("oi", "small_talk"),
    ("bom dia", "small_talk"),
    ("obg", "small_talk"),
    ("vlw", "small_talk"),
    ("tchau", "small_talk"),
    ("como vc s chama?", "assistant_identity"),
    ("qual seu nom", "assistant_identity"),
    ("qm e vc", "assistant_identity"),
    ("quem e voce", "assistant_identity"),
    ("que horas sao", "utility"),
    ("que dia e hoje", "utility"),
    ("o que voce pode fazer", "capabilities"),
    # "oq vc faz" → "o que voce faz" está no catálogo de capacidades (prioridade sobre identity.role).
    ("oq vc faz", "capabilities"),
    ("faz isso", "unclear_request"),
    ("arruma", "unclear_request"),
    # Não simples: consulta operacional / ferramenta / texto com dados.
    ("qual o estoque do produto 10080001?", None),
    ("liste os fornecedores do produto 10080001", None),
    ("pesquise na web sobre normas iso", None),
    ("coloque isso na lousa", None),
]


# Fallback honesto — pedidos não entendidos (Playbook, seções 11/28).
UNCLEAR_REQUEST_CASES = [
    ("faz isso", "action"),
    ("manda", "action"),
    ("arruma", "fix"),
    ("ajusta isso", "fix"),
    ("isso", "reference"),
    ("aquilo", "reference"),
    ("tira isso", "reference"),
    # Não deve acionar fallback (intenção clara ou contexto suficiente).
    ("estoque do produto 10080001", None),
    ("coloque isso na lousa", None),
    ("corrija o texto do e-mail", None),
]
