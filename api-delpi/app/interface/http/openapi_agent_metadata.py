"""Metadados OpenAPI para seleção de rotas pelo Minha DELPI Chat (embeddings + heurísticas)."""


def agent_route(*, summary: str, description: str, operation_id: str) -> dict:
    return {
        "summary": summary,
        "description": description,
        "operation_id": operation_id,
    }


PRODUCT_DETAIL = agent_route(
    summary="Dados cadastrais do produto",
    description=(
        "Retorna ficha cadastral completa de um código: descrição, tipo, unidade, grupo, custo, armazém, revisão e NCM. "
        "Use para cadastro, descrição ou atributos do item sem agregar estoque/preços. "
        "Para visão resumida com estoque e preços, prefira /summary; para ficha analítica ampla, /analyser."
    ),
    operation_id="get_product_detail",
)

PRODUCT_SUMMARY = agent_route(
    summary="Resumo do produto (cadastro + estoque + preços)",
    description=(
        "Consolida cadastro, amostra de estoque por filial e tabela de preços em uma consulta leve. "
        "Use para visão geral rápida do item quando não precisa de BOM, roteiro ou analisador completo."
    ),
    operation_id="get_product_summary",
)

PRODUCT_PARENTS = agent_route(
    summary="Onde o produto é usado (produtos pai / BOM reversa)",
    description=(
        "Lista produtos pai que consomem o código informado (explosão reversa / where-used). "
        "Use quando o usuário perguntar onde o item é usado, em quais PAs entra ou árvore de pais. "
        "Não confundir com estrutura filha (BOM) — use /structure."
    ),
    operation_id="get_product_parents",
)

PRODUCT_SUPPLIERS = agent_route(
    summary="Fornecedores do produto",
    description=(
        "Lista fornecedores vinculados ao item no cadastro/compras. "
        "Use para quem fornece, fornecedor principal ou histórico de fornecimento cadastral do código."
    ),
    operation_id="get_product_suppliers",
)

PRODUCT_CUSTOMERS = agent_route(
    summary="Clientes do produto",
    description=(
        "Lista clientes que compram ou estão vinculados ao item. "
        "Use para carteira de clientes do produto ou relacionamento comercial do código."
    ),
    operation_id="get_product_customers",
)

PRODUCT_INSPECTION = agent_route(
    summary="Inspeção de qualidade do produto (QP6/QP7/QP8)",
    description=(
        "Retorna dados de inspeção de qualidade e centros de trabalho de inspeção do item. "
        "Use para inspeção de qualidade, QP, CT de inspeção — não para expedição após inspeção final do PA. "
        "Para PA liberado para expedição (SHB010 + apontamento), use /shipping-status."
    ),
    operation_id="get_product_inspection",
)

PRODUCT_GUIDE = agent_route(
    summary="Roteiro de produção do produto",
    description=(
        "Lista o roteiro / sequência operacional (centros de trabalho, operações) do item. "
        "Use para roteiro, operações, CTs e sequência fabril do produto."
    ),
    operation_id="get_product_guide",
)

PRODUCT_INTERNAL_MOVEMENTS = agent_route(
    summary="Movimentações internas do produto",
    description=(
        "Movimentações internas de estoque/produção do item com filtros de período, filial, armazém, TM e OP. "
        "Use para movimentação interna, transferências ou histórico operacional do código."
    ),
    operation_id="get_product_internal_movements",
)

PRODUCT_SALES_BILLING = agent_route(
    summary="Faturamento do produto",
    description=(
        "Resumo de faturamento e notas fiscais de saída vinculadas ao código. "
        "Use para faturamento, NF de venda ou receita faturada do item — distinto de carteira em aberto (/sales/open-orders)."
    ),
    operation_id="get_product_sales_billing",
)

PRODUCT_INBOUND_INVOICE_ITEMS = agent_route(
    summary="Itens de nota fiscal de entrada do produto",
    description=(
        "Lista itens de notas fiscais de entrada (compras) vinculados ao código. "
        "Use para NF de entrada, documentos de compra ou recebimento do item."
    ),
    operation_id="get_product_inbound_invoice_items",
)

PRODUCT_OUTBOUND_INVOICE_ITEMS = agent_route(
    summary="Itens de nota fiscal de saída do produto",
    description=(
        "Lista itens de notas fiscais de saída (vendas) vinculados ao código. "
        "Use para NF de saída ou faturamento documental do item — distinto de /sales/billing agregado."
    ),
    operation_id="get_product_outbound_invoice_items",
)

PRODUCT_PRICING = agent_route(
    summary="Preços e tabelas comerciais do produto",
    description=(
        "Tabelas de preço, condições comerciais e valores de venda do item. "
        "Use para preço de venda, tabela comercial ou valor unitário — não para custo/CPV agregado de suprimentos."
    ),
    operation_id="get_product_pricing",
)

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

PRODUCT_STRUCTURE_EXCLUSIVITY = agent_route(
    summary="Estrutura do produto com exclusividade de matérias-primas",
    description=(
        "Abre a BOM vigente multinível e marca MPs exclusivas (presentes em apenas um PA válido). "
        "Use para estrutura com exclusividade, MPs exclusivas e quantidade acumulada por componente."
    ),
    operation_id="get_product_structure_exclusivity",
)

EXCLUSIVE_RAW_MATERIALS_CATALOG = agent_route(
    summary="Catálogo global de matérias-primas exclusivas",
    description=(
        "Lista MPs exclusivas (presentes em apenas um PA válido) ou PAs que possuem MPs exclusivas, "
        "sem informar código de produto na pergunta. "
        "Use view=by_material para «quais matérias-primas são exclusivas?» e "
        "view=by_finished_product para «quais produtos têm MP exclusiva?». "
        "Para estrutura detalhada de um PA específico, prefira /structure/exclusivity."
    ),
    operation_id="list_exclusive_raw_materials_catalog",
)

PRODUCT_PRODUCTION_STATUS = agent_route(
    summary="Situação produtiva do produto (PA, PI, OP e apontamentos)",
    description=(
        "Avalia PA e intermediários com OPs da SC2010 e apontamentos da SH6010 em uma data de referência. "
        "Use para saber se produção iniciou, quanto foi apontado e equivalente em PA."
    ),
    operation_id="get_product_production_status",
)

PRODUCT_SHIPPING_STATUS = agent_route(
    summary="Expedição do PA via inspeção final",
    description=(
        "Retorna quantidade finalizada para expedição e perdas no CT de inspeção final (SHB010 + SH6010). "
        "Use para saber se o PA já passou pela inspeção final e quanto está liberado para expedição."
    ),
    operation_id="get_product_shipping_status",
)

PRODUCT_FACTORY_STATUS = agent_route(
    summary="Status fabril completo do produto",
    description=(
        "Visão consolidada: estrutura vigente, MPs exclusivas, estoque de MPs, produção, expedição e status fabril. "
        "Preferir quando o usuário pedir status completo do produto na fábrica ou visão fabril integrada."
    ),
    operation_id="get_product_factory_status",
)

PRODUCT_COST_IMPACT_SIMULATION = agent_route(
    summary="Simulador de impacto de custos do PA",
    description=(
        "Ranking das matérias-primas que mais impactam o custo de 1 PA, com base na BOM vigente (SG1010). "
        "Suporta custo padrão ou última compra e simulação percentual de reajuste (adjustment_percent). "
        "Use para perguntas sobre materiais críticos de custo, Pareto de MPs ou simulação de aumento de preço."
    ),
    operation_id="get_product_cost_impact_simulation",
)

PRODUCT_LAST_PURCHASE = agent_route(
    summary="Última compra válida da matéria-prima",
    description=(
        "Retorna a última NF de entrada válida (SD1010) com fornecedor, preço unitário, ICMS e pedido vinculado. "
        "Exclui transportadoras e fornecedores internos. Use para último fornecedor ou última aquisição de MP."
    ),
    operation_id="get_product_last_purchase",
)

PRODUCT_PURCHASE_PRICE_HISTORY = agent_route(
    summary="Histórico de preço de compra da matéria-prima",
    description=(
        "Série temporal de NFs de entrada com preço unitário, ICMS e variação percentual entre compras consecutivas. "
        "Filtrável por período e filial."
    ),
    operation_id="get_product_purchase_price_history",
)

PRODUCT_PURCHASE_BUDGET_HISTORY = agent_route(
    summary="Histórico de orçamento de compra (SC + PC)",
    description=(
        "Unifica solicitações de compra (SC1010) e pedidos de compra (SC7010) para análise de cotação e requisição."
    ),
    operation_id="get_product_purchase_budget_history",
)

PRODUCT_RAW_MATERIAL_PRICE_INTELLIGENCE = agent_route(
    summary="Análise inteligente de preço de matéria-prima",
    description=(
        "Visão consolidada: cadastro, última compra, ICMS, histórico de orçamento, variação de preço e status. "
        "Preferir quando o usuário pedir análise completa de preço/custo de compra de uma MP."
    ),
    operation_id="get_product_raw_material_price_intelligence",
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
        "Consolida cadastro, estrutura, roteiro e inspeção. Default view=full. "
        "Use view=summary para amostra leve. Para intenção pontual prefira rotas granulares: "
        "/stock (estoque), /structure (BOM), /guide (roteiro), /inspection (qualidade), "
        "/summary (cadastro+estoque+preços) ou /factory-status (visão fabril integrada)."
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

LMP_DASHBOARD_SUMMARY = agent_route(
    summary="KPIs resumidos do painel de LMPs",
    description=(
        "Retorna métricas agregadas do dashboard de LMPs (totais, percentual no prazo, lead time). "
        "Preferir no chat para KPIs ou resumo de LMPs — não o dashboard completo com itens e gráficos."
    ),
    operation_id="get_lmps_dashboard_summary",
)

LMP_DASHBOARD_ITEMS = agent_route(
    summary="Itens paginados do painel de LMPs",
    description=(
        "Lista paginada de LMPs do dashboard com filtros de período, filial e status. "
        "Uso principal do MFE; no chat prefira /dashboard/summary para KPIs ou /lmps para listagem."
    ),
    operation_id="list_lmps_dashboard_items",
)

LMP_DASHBOARD_CHARTS = agent_route(
    summary="Gráficos do painel de LMPs",
    description=(
        "Dados para gráficos do dashboard de LMPs (nível, status, evolução). "
        "Uso principal do MFE — no chat prefira /dashboard/summary."
    ),
    operation_id="get_lmps_dashboard_charts",
)

TRANSFORMA_MAIS_LIST = agent_route(
    summary="Listar processos Transforma Mais",
    description=(
        "Lista processos de melhoria contínua (Transforma Mais) com filtros de filial, setor e status. "
        "Use para melhoria contínua e processos Transforma Mais — não confundir com LMP de engenharia."
    ),
    operation_id="list_transforma_mais_processes",
)

TRANSFORMA_MAIS_SUMMARY = agent_route(
    summary="Resumo Transforma Mais",
    description=(
        "KPIs agregados dos processos Transforma Mais por filial e período. "
        "Preferir no chat para resumo de melhoria contínua vs listagem completa de processos."
    ),
    operation_id="get_transforma_mais_summary",
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

SUPPLIES_NEGOTIATION_SAVINGS = agent_route(
    summary="Economia em negociações de compras (planilha IDD Suprimentos)",
    description=(
        "Soma da economia em reais por filial e período, lida da aba "
        "economia_negociacoes_compra (Google Sheets). "
        "Use para o indicador estratégico supplies_negotiation_savings / IDD Suprimentos."
    ),
    operation_id="get_supplies_negotiation_savings_summary",
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
