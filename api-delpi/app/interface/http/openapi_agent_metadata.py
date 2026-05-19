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

SUPPLIES_STOCK_VALUE = agent_route(
    summary="Valor total de estoque (suprimentos)",
    description=(
        "Métrica agregada do valor total de estoque da empresa ou filial — indicador de suprimentos. "
        "Não usar para saldo de um produto/código; para item use estoque do produto (/products/{code}/stock)."
    ),
    operation_id="get_supplies_stock_value",
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
