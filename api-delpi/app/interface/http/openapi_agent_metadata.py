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
        "Exclui transportadoras, fornecedores internos e NF de frete (D1_QUANT zero na MP). "
        "Use para último fornecedor ou última aquisição de MP."
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

PRODUCT_DIRECTIVES = agent_route(
    summary="Diretivas do produto (referência cliente ou código DELPI)",
    description=(
        "Resolve um PA pelo código DELPI (9026xxxx) ou pela referência do cliente (SB1010.B1_REFEREN) "
        "e retorna visão integrada: código DELPI, estrutura multinível, matérias-primas, "
        "fornecedores com part number (SA5010) e última NF de compra válida de cada MP (SD1010). "
        "Use para perguntas como «diretivas 90260882», «diretivas 10018137», "
        "«referência do cliente», «BOM com fornecedores e última compra»."
    ),
    operation_id="get_product_directives",
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

LIST_PRODUCT_DRAWINGS = agent_route(
    summary="Catálogo de desenhos PDF da biblioteca",
    description=(
        "Lista paginada dos PDFs técnicos DELPI disponíveis na biblioteca corporativa. "
        "Permite filtrar por código, filename, revisão, variante, tamanho e data de modificação. "
        "Use para auditar a biblioteca, localizar desenhos para análise ou validar cobertura por prefixo."
    ),
    operation_id="list_product_drawings",
)

PRODUCT_DRAWING_METADATA = agent_route(
    summary="Metadados do desenho PDF do produto",
    description=(
        "Localiza o PDF técnico DELPI na biblioteca corporativa pelo código do produto. "
        "Retorna filename, revisão, tamanho e data de modificação. "
        "Para baixar o arquivo use /products/{code}/drawing/pdf."
    ),
    operation_id="get_product_drawing",
)

PRODUCT_DRAWING_PDF = agent_route(
    summary="Download do desenho PDF do produto",
    description=(
        "Retorna o PDF técnico DELPI da biblioteca corporativa para o código informado. "
        "Resposta binária application/pdf (inline). "
        "Prefira /products/{code}/drawing quando só precisar saber se o arquivo existe."
    ),
    operation_id="get_product_drawing_pdf",
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

MINI_APPLICATORS_FERRAMENTAS_LIST = agent_route(
    summary="Listar ferramentas mini-aplicadores",
    description=(
        "Lista ferramentas dos grupos Protheus 23 e 24 (mini-aplicadores). "
        "Filtros opcionais: codigo, descricao, filial."
    ),
    operation_id="list_mini_applicators_ferramentas",
)

MINI_APPLICATORS_FERRAMENTA_GET = agent_route(
    summary="Detalhe de ferramenta mini-aplicador",
    description="Retorna cadastro SB1010 de uma ferramenta mini-aplicador pelo código.",
    operation_id="get_mini_applicators_ferramenta",
)

MINI_APPLICATORS_PECAS_LIST = agent_route(
    summary="Listar peças do mini-aplicador",
    description="Lista peças amarradas à ferramenta (SG1010 + SB1010 grupo 3019).",
    operation_id="list_mini_applicators_pecas",
)

MINI_APPLICATORS_GOLPES_GET = agent_route(
    summary="Golpes do mini-aplicador no período",
    description=(
        "Soma consumo SD4010 da ferramenta no período, filtrando apontamentos SH6010 "
        "por data/hora (legado MiniAplicadores). Aceita ISO date ou datetime em data_inicial/data_final."
    ),
    operation_id="get_mini_applicators_golpes",
)

MINI_APPLICATORS_COMPONENTES_LIST = agent_route(
    summary="Componentes do mini-aplicador",
    description=(
        "Explosão recursiva da estrutura (SG1010) com estoque nos locais 01 e 99 "
        "para a filial informada."
    ),
    operation_id="list_mini_applicators_componentes",
)

LMP_BY_SALE = agent_route(
    summary="Detalhe da LMP por ordem de venda",
    description=(
        "Carrega uma LMP específica pelo número da ordem de venda (OV/proposta), "
        "com produtos, cliente, vendedor, resumo de engenharia e classificação "
        "(nível, SLA, lead time útil, status). "
        "O histórico AIJ010 fica em rotas dedicadas `/history/events` e `/history/flow`. "
        "Use quando houver número de OV, ordem de venda ou referência explícita a uma LMP individual. "
        "Parâmetros opcionais `date_start`, `date_end` e `branch` alinham o escopo ao dashboard/MFE. "
        "Não confundir OV com código de produto."
    ),
    operation_id="get_lmp_by_sale_number",
)

LMP_HISTORY_EVENTS = agent_route(
    summary="Histórico de eventos da OV (AIJ010)",
    description=(
        "Lista eventos do histórico da ordem de venda sem joins pesados por linha. "
        "Use para timeline/tabela do detalhe da LMP. "
        "Parâmetros `date_start`, `date_end` e `branch` alinham o contexto do painel; "
        "`revision` filtra uma revisão específica."
    ),
    operation_id="get_lmp_history_events",
)

LMP_HISTORY_FLOW = agent_route(
    summary="Transições de fluxo da engenharia na OV",
    description=(
        "Retorna apenas eventos de engenharia com contexto anterior/próximo para "
        "identificar entradas, avanços e retornos. Consulta leve e separada do histórico completo."
    ),
    operation_id="get_lmp_history_flow",
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

PRODUCTION_OTD = agent_route(
    summary="OTD produção — resumo e ordens (SC2010)",
    description=(
        "Painel de OTD de produção: resumo (OPs no prazo/atrasadas, % OTD) e listagem paginada "
        "de ordens finalizadas (SC2010 com C2_DATPRF × C2_DATRF). "
        "Considera apenas OP mãe (C2_SEQUEN = '001', sufixo …001 em C2_OP), excluindo OPs vinculadas. "
        "Parâmetros sort_by e sort_dir ordenam a listagem paginada no servidor. "
        "Use para listar OPs atrasadas ou no prazo, detalhar entrega de produção ou exportar ordens. "
        "Para apenas o percentual agregado sem listagem, prefira GET /production/on_time_delivery_pct. "
        "Para série temporal, use GET /production/otd/series. "
        "Não confundir com OTD de compras (/supplies/otd) nem OTD comercial de pedidos de venda."
    ),
    operation_id="get_production_otd",
)

PRODUCTION_OEE = agent_route(
    summary="OEE produção — resumo e apontamentos (view fabril)",
    description=(
        "Painel de eficiência de produção alinhado à eficiência fabril: mesma view "
        "(vw_Apontamentos_Eficiencia), STATUS_REGISTRO=OK, CTs excluídos e faixa 0–199%. "
        "Resumo e listagem usam EFICIENCIA_PERCENTUAL (tempo previsto ÷ tempo real); "
        "detalhe SH6010 calcula a mesma métrica a partir de roteiro e horários. "
        "Parâmetros sort_by e sort_dir ordenam a listagem paginada no servidor. "
        "status=valid|outlier filtra apontamentos dentro ou fora da faixa 0–199%. "
        "efficiency_bands=ok,low,verify (csv) filtra por faixa: na faixa (≥50%), eficiência baixa (<50%) "
        "ou fora da faixa (outlier); tem precedência sobre status quando informado. "
        "product_type=PA|PI filtra pelo tipo do produto (SB1010.B1_TIPO). "
        "Para detalhe (roteiro SG2, estrutura BOM, tempos), use GET /production/oee/appointments/{appointment_id}. "
        "Para série temporal, use GET /production/oee/series. "
        "Listagem dedicada MOD/gráficos: GET /production/eficiencia-fabril/*."
    ),
    operation_id="get_production_oee",
)

PRODUCTION_OEE_APPOINTMENT = agent_route(
    summary="Detalhe do apontamento OEE (roteiro, estrutura e tempos)",
    description=(
        "Retorna análise composta de um apontamento SH6010 (R_E_C_N_O_ / appointment_id): "
        "cadastro do apontamento (OP, produto PA/PI, CT, operação, operador, recurso, quantidades), "
        "time_analysis (setup, fator padrão, horas previstas/reais, eficiência por tempos, "
        "findings com motivos/alertas automáticos), "
        "routing_operations (roteiro SG2010 com operação do apontamento destacada) e "
        "structure (BOM do produto em árvore). Parâmetro branch opcional restringe a filial. "
        "Use quando o usuário pedir detalhe do apontamento, roteiro, estrutura ou cálculo de tempos "
        "previsto × realizado de um registro OEE ou eficiência fabril — não para listagem paginada do período. "
        "Rota compartilhada pelo painel OEE e pelo MFE de eficiência fabril."
    ),
    operation_id="get_production_oee_appointment_by_id",
)

PRODUCTION_EFICIENCIA_FABRIL_DASHBOARD = agent_route(
    summary="Eficiência fabril — dashboard MOD e gráficos",
    description=(
        "Painel de eficiência fabril: KPIs (eficiência média na faixa 0–199%, resultado MOD, "
        "horas ganhas/perdidas), gráficos por dia/operador/centro de trabalho e listagem paginada "
        "de apontamentos (view vw_Apontamentos_Eficiencia; `appointment_id` via SH6010). "
        "Use para eficiência fabril, resultado MOD, dashboard gerencial de apontamentos ou análise por CT/operador. "
        "Parâmetros: date_start, date_end (obrigatórios), branch, op, employee, work_center, page, page_size. "
        "Não confundir com GET /production/oee (painel OEE com mesma view, foco SH6010) nem com "
        "GET /production/overall_equipment_effectiveness_pct (percentual agregado). "
        "Detalhe de um apontamento: GET /production/oee/appointments/{appointment_id}."
    ),
    operation_id="get_eficiencia_fabril_dashboard",
)

PRODUCTION_EFICIENCIA_FABRIL_APPOINTMENTS = agent_route(
    summary="Eficiência fabril — apontamentos (carga bulk)",
    description=(
        "Lista completa de apontamentos de eficiência fabril no período (sem paginação server-side). "
        "Use para volume total de apontamentos no intervalo ou integrações que recalculam localmente. "
        "Para KPIs, gráficos e paginação, prefira GET /production/eficiencia-fabril/dashboard."
    ),
    operation_id="list_eficiencia_fabril_appointments",
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

PRODUCTION_CONSUMPTION_TOP_ITEMS = agent_route(
    summary="Itens mais consumidos na produção",
    description=(
        "Ranking de itens com maior consumo real (SD4010) no período, usando a fórmula "
        "D4_QTDEORI - D4_QUANT. Use para «itens mais consumidos», «maior consumo» ou "
        "«ranking de consumo» — não confundir com estoque ou compras."
    ),
    operation_id="get_production_consumption_top_items",
)

PURCHASES_TOP_PRODUCTS = agent_route(
    summary="Produtos mais comprados no período",
    description=(
        "Ranking agregado de produtos mais comprados (SD1010) por quantidade e valor, "
        "excluindo transportadoras, fornecedores internos e NF de frete (quantidade zero). "
        "Use para «produtos mais comprados» ou ranking de compras — não para última compra de um item."
    ),
    operation_id="get_purchases_top_products",
)

PRODUCTION_LOSSES_TOP_MATERIALS = agent_route(
    summary="Matérias-primas com mais refugo/scrap no período",
    description=(
        "Ranking agregado de perdas de matéria-prima (SBC010) por quantidade e ocorrências. "
        "Use para «refugos de MP», «scrap no período» ou «matérias-primas com mais perda»."
    ),
    operation_id="get_production_losses_top_materials",
)

PRODUCTION_LOSSES_RECORDS = agent_route(
    summary="Registros detalhados de refugo/scrap",
    description=(
        "Lista linha a linha os registros de perda de matéria-prima (SBC010) no período. "
        "Use quando o usuário pedir detalhe de refugos, motivo ou OP da perda."
    ),
    operation_id="get_production_losses_records",
)

PRODUCTION_SCHEDULE_TODAY = agent_route(
    summary="Produtos programados para produzir na data",
    description=(
        "Lista produtos acabados com OP ativa e operação programada para a data de referência "
        "(SC2010 + SH8010). Use para «programados hoje», «produzir hoje» ou plano diário de PCP."
    ),
    operation_id="get_production_schedule_today",
)

PRODUCTION_ORDERS_OPEN = agent_route(
    summary="OPs em aberto na data",
    description=(
        "Lista ordens de produção programadas para a data que ainda não foram finalizadas "
        "(C2_QUANT > C2_QUJE). Use para backlog do dia, OPs pendentes ou em execução."
    ),
    operation_id="get_production_orders_open",
)

PRODUCTION_ORDER_BY_OP = agent_route(
    summary="Detalhe da OP por C2_OP",
    description=(
        "Retorna cadastro SC2010 da ordem de produção com datas, quantidades, status OTD "
        "e metadados do produto. Use product_type=PA ou product_type=PI para filtrar pelo "
        "tipo SB1010.B1_TIPO (PA exige C2_PRODUTO com prefixo 9 ou 8; sequência 001 preferencial). "
        "Inclui linked_orders: demais OPs com o mesmo C2_NUM (PA ou PI, exceto a consultada). "
        "Use linked_sort_by e linked_sort_dir para ordenar linked_orders no servidor. "
        "Inclui related_routes para /products/{code}, /summary, /guide e /stock."
    ),
    operation_id="get_production_order_by_op",
)

PRODUCTION_ORDERS_FINISHED = agent_route(
    summary="OPs finalizadas na data",
    description=(
        "Lista ordens de produção finalizadas na data de referência (C2_QUANT = C2_QUJE). "
        "Use para produção concluída no dia."
    ),
    operation_id="get_production_orders_finished",
)

PRODUCTION_WORK_CENTER_ORDER_SUMMARY = agent_route(
    summary="Resumo de OPs por centro de trabalho",
    description=(
        "Conta OPs finalizadas e em aberto agrupadas por centro de trabalho (CT) na data. "
        "Use para balanceamento de carga e status produtivo por CT."
    ),
    operation_id="get_production_work_center_order_summary",
)

PRODUCTION_CONSUMPTION_TOP_ITEMS_BY_WORK_CENTER = agent_route(
    summary="Consumo por centro de trabalho",
    description=(
        "Ranking de itens consumidos/empenhados agrupados por CT planejado (SD4010 + SH8010). "
        "Use para consumo por centro de trabalho ou CT específico."
    ),
    operation_id="get_production_consumption_top_items_by_work_center",
)

PRODUCTION_CONSUMPTION_TOP_ITEMS_VALIDATED = agent_route(
    summary="Consumo validado por apontamento real",
    description=(
        "Ranking de consumo real com EXISTS em apontamentos SH6010 tipo produção. "
        "Use quando o usuário pedir consumo validado ou confirmado por apontamento."
    ),
    operation_id="get_production_consumption_top_items_validated",
)

PRODUCTION_ALLOCATION_GAPS = agent_route(
    summary="Componentes sem empenho (travamento)",
    description=(
        "Lista componentes de OPs ativas com D4_QUANT = 0 no CT e data informados. "
        "Use para travamento de produção por ausência de empenho."
    ),
    operation_id="get_production_allocation_gaps",
)

PRODUCTION_ORDERS_FINISHED_WITHOUT_CONSUMPTION = agent_route(
    summary="OPs finalizadas sem consumo de componentes",
    description=(
        "Identifica OPs finalizadas (C2_QUANT = C2_QUJE) sem baixa de material no CT/data. "
        "Use para auditoria de apontamento e inconsistências produtivas."
    ),
    operation_id="get_production_orders_finished_without_consumption",
)

PRODUCTION_WORK_CENTER_AVERAGE_PLANNED_TIME = agent_route(
    summary="Tempo médio planejado por centro de trabalho",
    description=(
        "Média de horas planejadas (H8_HRINI → H8_HRFIM) por CT em OPs finalizadas na data. "
        "Use para análise de tempo planejado por centro de trabalho."
    ),
    operation_id="get_production_work_center_average_planned_time",
)

PRODUCTION_CONSUMPTION_BY_ITEM = agent_route(
    summary="Consumo real de item por produto",
    description=(
        "Apura consumo real (D4_QTDEORI - D4_QUANT) de um item por produto pai, "
        "opcionalmente filtrado por grupo. Path: /production/consumption/by-item/{code}."
    ),
    operation_id="get_production_consumption_by_item",
)

PRODUCTION_PLANNED_VS_REAL_TIME = agent_route(
    summary="Tempo planejado × tempo real por OP",
    description=(
        "Compara tempo planejado (setup + hora-mil × quantidade em milheiro) "
        "com tempo real de apontamento para OPs finalizadas na data. "
        "Classifica desempenho em OK, ATENCAO ou ESTOURO."
    ),
    operation_id="get_production_planned_vs_real_time",
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

QUALITY_KAIZEN_SUMMARY = agent_route(
    summary="Kaizens — resumo e listagem (PostgreSQL)",
    description=(
        "Resumo de melhorias kaizen cadastradas: total no período, "
        "economia acumulada (daily_savings × dias ativos) e list_kaizen. "
        "Parâmetros: title, status, branch, date_start, date_end. "
        "Sem date_start/date_end na listagem retorna todos os kaizens implantados "
        "(útil para catálogo completo no dashboard). "
        "Campos calculados: daily_savings, annual_savings (daily_savings × 365). "
        "Para detalhe de um kaizen (parâmetros do cálculo, investimento, responsável), "
        "use GET /quality/kaizens/{kaizen_id} com o id retornado em list_kaizen[].id."
    ),
    operation_id="get_kaizen_summary",
)

QUALITY_KAIZEN_BY_ID = agent_route(
    summary="Detalhe do kaizen (PostgreSQL)",
    description=(
        "Retorna ficha completa de um kaizen pelo UUID do cadastro ou, para registros "
        "migrados da planilha, pelo id legado composto (filial-data-título). "
        "Inclui título, status, setor, unidade, responsável, investimento, daily_savings, "
        "annual_savings e entradas do cálculo (seconds_per_occurrence, occurrences_per_day, "
        "hourly_cost, hours_saved_per_day). "
        "Use quando o usuário pedir detalhe, ficha ou economia projetada de um kaizen específico — "
        "não para resumo agregado do período (prefira GET /quality/kaizens/summary)."
    ),
    operation_id="get_kaizen_by_id",
)

QUALITY_KAIZEN_RECORDS_LIST = agent_route(
    summary="Cadastro operacional de kaizens (PostgreSQL)",
    description=(
        "Lista paginada de kaizens cadastrados no PostgreSQL (cadastro operacional). "
        "Filtros: filial, status, tipo de economia, título, período. "
        "Use para «kaizens cadastrados», «registros kaizen», «cadastro kaizen» — "
        "ou para edição/CRUD quando o usuário precisa alterar um registro."
    ),
    operation_id="list_kaizen_records",
)

QUALITY_KAIZEN_RECORD_BY_ID = agent_route(
    summary="Detalhe do kaizen cadastrado (PostgreSQL)",
    description=(
        "Retorna ficha completa de um kaizen pelo UUID do cadastro operacional. "
        "Use após list_kaizen_records quando o usuário pedir detalhe de um registro específico."
    ),
    operation_id="get_kaizen_record",
)

FINANCIAL_ROL = agent_route(
    summary="ROL financeiro (receita operacional líquida)",
    description=(
        "Indicador ROL financeiro consolidado por filial e período. "
        "Use para «rol financeiro», «receita operacional líquida», «qual o rol» no contexto financeiro — "
        "não confundir com ROL comercial (/commercial/rol/series) ou metas comerciais."
    ),
    operation_id="get_financial_rol",
)

FINANCIAL_EBITDA = agent_route(
    summary="EBITDA percentual (financeiro)",
    description=(
        "Percentual de EBITDA sobre ROL no período e filial informados. "
        "Use quando o usuário mencionar EBITDA, margem EBITDA ou indicador financeiro de EBITDA."
    ),
    operation_id="get_financial_ebitda_pct",
)

FINANCIAL_FIXED_COST = agent_route(
    summary="Custo fixo percentual (financeiro)",
    description=(
        "Percentual de custos fixos sobre ROL. "
        "Use para «custo fixo», «custos fixos percentual» ou estrutura de custo fixo da empresa."
    ),
    operation_id="get_financial_fixed_cost_pct",
)

FINANCIAL_PMR = agent_route(
    summary="PMR — prazo médio de recebimento",
    description=(
        "Prazo médio de recebimento (PMR) por filial e período. "
        "Use para «pmr», «prazo médio de recebimento» ou inadimplência/recebíveis agregados."
    ),
    operation_id="get_financial_pmr",
)

COMMERCIAL_PROPOSALS = agent_route(
    summary="Propostas comerciais (carteira Totvs)",
    description=(
        "Lista paginada de propostas comerciais com filtros de filial, período e status "
        "(ganhas, abertas ou todas). "
        "Parâmetros sort_by e sort_dir ordenam a listagem paginada no servidor. "
        "Use search para filtrar por proposta, descrição, status, cliente e demais colunas visíveis. "
        "Use para «propostas comerciais», «listar propostas», «propostas ganhas» — "
        "distinto de propostas internas PDF (/propostas-comerciais/) ou taxa de fechamento (/closing-rate)."
    ),
    operation_id="list_commercial_proposals",
)

COMMERCIAL_PROPOSAL_DETAIL = agent_route(
    summary="Detalhe da proposta comercial (OV)",
    description=(
        "Cabeçalho da OV no TOTVS (AD1010) por filial, número e revisão. "
        "Use para detalhar proposta comercial do dashboard — distinto da listagem paginada."
    ),
    operation_id="get_commercial_proposal",
)

COMMERCIAL_PROPOSAL_HISTORY_EVENTS = agent_route(
    summary="Histórico de estágios da proposta comercial",
    description=(
        "Eventos AIJ010 da OV (processo/estágio/status) para o painel comercial. "
        "Mesmo domínio do histórico LMP, exposto sob /commercial para o dashboard comercial."
    ),
    operation_id="get_commercial_proposal_history_events",
)
