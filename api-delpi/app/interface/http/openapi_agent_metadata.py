"""Metadados OpenAPI para seleção de rotas pelo Minha DELPI Chat (embeddings + heurísticas)."""


def agent_route(*, summary: str, description: str, operation_id: str) -> dict:
    return {
        "summary": summary,
        "description": description,
        "operation_id": operation_id,
    }


PRODUCT_SEARCH = agent_route(
    summary="Buscar produtos no Protheus",
    description=(
        "Consulta paginada por código, grupo ou descrição parcial. "
        "Preferir quando o usuário não informou o código exato do item ou quer localizar um produto. "
        "Não usar para estoque por filial/armazém de um código já conhecido — use estoque do produto."
    ),
    operation_id="search_products",
)

PRODUCT_STRUCTURE = agent_route(
    summary="Estrutura (BOM) do produto",
    description=(
        "Lista a estrutura / lista de materiais (BOM) de um produto a partir do código. "
        "Use para árvore de componentes, itens filhos e explosão de estrutura."
    ),
    operation_id="get_product_structure",
)

PRODUCT_STOCK = agent_route(
    summary="Estoque do produto por filial e local",
    description=(
        "Saldo e posição de estoque de um item específico (código no path). "
        "Use para perguntas como estoque, saldo, disponível, quantidade em armazém de um produto. "
        "Não confundir com valor total de estoque da empresa (rota de suprimentos /stock-value)."
    ),
    operation_id="get_product_stock",
)

PRODUCT_ANALYSER = agent_route(
    summary="Analisador completo do produto",
    description=(
        "Resumo consolidado do item: descrição, tipo, unidade, grupo, roteiro, fornecedores e demais "
        "visões em uma única consulta. Preferir para descrição do produto, ficha resumida ou "
        "visão geral quando não basta só o estoque."
    ),
    operation_id="get_product_analyser",
)

LMP_LIST = agent_route(
    summary="Listar LMPs (ordens especiais / amostras)",
    description=(
        "Lista paginada de LMPs com filtros de período, filial e tipo (LMP, Amostra, Outro). "
        "Use para listar, filtrar ou pesquisar várias ordens — não para detalhe de uma OV específica."
    ),
    operation_id="list_lmps",
)

LMP_DASHBOARD = agent_route(
    summary="Dashboard de LMPs",
    description=(
        "Painel agregado de LMPs com filtro de status. "
        "Use quando o usuário pedir dashboard, painel, resumo ou visão gerencial de LMPs."
    ),
    operation_id="list_lmps_dashboard",
)

LMP_BY_SALE = agent_route(
    summary="Detalhe da LMP por ordem de venda",
    description=(
        "Carrega uma LMP específica pelo número da ordem de venda (OV). "
        "Use quando houver número de OV, ordem de venda ou referência explícita a uma LMP individual."
    ),
    operation_id="get_lmp_by_sale_number",
)

SUPPLIES_CPV = agent_route(
    summary="CPV — custo de produto vendido (Kardex / suprimentos)",
    description=(
        "Indicador CPV agregado por filial e período (SD2010, SUM(D2_CUSTO1), CFOPs Kardex). "
        "Use quando o usuário mencionar CPV, custo de produto vendido ou ranking de custo em suprimentos. "
        "Não usar para estoque de um produto nem valor total de estoque da empresa."
    ),
    operation_id="get_supplies_cpv",
)

SUPPLIES_OTD = agent_route(
    summary="OTD — entrega no prazo (suprimentos)",
    description=(
        "Indicador OTD (on-time delivery) de compras/suprimentos por filial e período. "
        "Use para perguntas sobre OTD, entrega no prazo ou atrasos de fornecimento agregados. "
        "Não confundir com OTD de produção ou entrega de pedido de venda de um produto específico."
    ),
    operation_id="get_supplies_otd",
)

SUPPLIES_INVENTORY_TURNOVER = agent_route(
    summary="Giro de estoque / IDD (suprimentos)",
    description=(
        "Giro de estoque (IDD) por filial, local e período: estoque ÷ CPV médio mensal. "
        "O valor de estoque usa o mesmo método de /supplies/stock-value "
        "(SB2 atual sem datas; SB9010+SD3010 estimado com start_date e end_date). "
        "CPV vem de SD2010 (D2_CUSTO1, D2_EMISSAO) no período, CFOPs Kardex 5101/5124/6101/6124. "
        "Use para giro, rotatividade ou IDD — não para saldo de um item."
    ),
    operation_id="get_supplies_inventory_turnover",
)

SUPPLIES_STOCK_VALUE = agent_route(
    summary="Valor total de estoque (suprimentos)",
    description=(
        "Métrica agregada do valor total de estoque da empresa ou filial — indicador de suprimentos. "
        "Sem start_date/end_date: saldo atual em SB2010 (B2_VATU1). "
        "Com start_date e end_date: estimativa histórica pelo último fechamento em SB9010 (B9_VINI1) "
        "mais movimentações líquidas em SD3010 até o fim do período "
        "(entrada D3_TM < '500', saída caso contrário; intervalo [start_date, end_date] inclusivo, "
        "fim exclusivo no dia seguinte). Retorna bloco estimation quando histórico. "
        "location filtra SB9/SD3 no modo histórico. "
        "Não usar para saldo de um produto/código; para item use estoque do produto (/products/{code}/stock). "
        "Detalhes: docs/api/supplies-estoque-historico.md."
    ),
    operation_id="get_supplies_stock_value",
)

PRODUCT_PURCHASES = agent_route(
    summary="Histórico de compras do produto",
    description=(
        "Lista compras / entradas de um item pelo código no path. "
        "Use quando o usuário pedir histórico de compras, últimas compras ou fornecimento do produto."
    ),
    operation_id="get_product_purchases",
)

PRODUCT_SALES_SUMMARY = agent_route(
    summary="Resumo de vendas do produto",
    description=(
        "Resumo de vendas e faturamento de um item específico. "
        "Use para vendas, faturamento ou performance comercial de um código."
    ),
    operation_id="get_product_sales_summary",
)

PRODUCT_SALES_OPEN_ORDERS = agent_route(
    summary="Carteira de pedidos de venda em aberto do produto",
    description=(
        "Pedidos de venda em aberto (carteira) vinculados ao código do produto. "
        "Use para carteira, pedidos abertos ou backlog de vendas do item."
    ),
    operation_id="get_product_sales_open_orders",
)

SALE_ORDERS_LIST = agent_route(
    summary="Listar ordens de venda",
    description=(
        "Lista paginada de ordens de venda (OV) por período. "
        "Use para listar OVs, pedidos de venda ou vendas no período — não para detalhe de LMP de uma OV."
    ),
    operation_id="list_sale_orders",
)

DATA_SQL = agent_route(
    summary="Executar consulta SQL somente leitura",
    description=(
        "Executa SELECT (com CTE e recursivo permitido) no Protheus. "
        "Corpo JSON com campo sql ou text/plain com a query. "
        "Requer permissão api-delpi.data ou api-delpi.access.full."
    ),
    operation_id="execute_readonly_sql",
)
