export const helpTooltips = {
  home: "Painel inicial do Financeiro: receita líquida, margem EBITDA, custo fixo, prazo médio de recebimento, pontualidade de pagamento dos clientes e as maiores despesas do período.",
  rol: "Receita operacional líquida do período — faturamento menos os impostos sobre venda. Clique para abrir a composição, a evolução e o ranking de clientes.",
  billing:
    "Faturamento operacional do período: receita bruta, descontos, devoluções e impostos até chegar na ROL. A série e o ranking de clientes usam a mesma base TOTVS do dashboard comercial.",
  billingSeries:
    "Evolução da ROL na visão mensal: últimos 12 meses ancorados no fim do período filtrado. Com consolidado, compara Santa Catarina e Espírito Santo.",
  billingWaterfall:
    "Demonstração da ROL: a receita bruta menos descontos, devoluções e impostos sobre venda, com o saldo a cada linha.",
  billingCustomers:
    "Clientes com maior ROL no período e a fatia de cada um sobre o total filtrado.",
  billingUnits: "ROL por unidade operacional no mesmo recorte de datas.",
  ebitda: "Resultado operacional antes de juros, impostos, depreciação e amortização, sobre a receita líquida.",
  fixedCost: "Peso do custo fixo sobre a receita líquida. Quanto menor, mais folga a operação tem para oscilação de volume.",
  pmr: "Prazo médio de recebimento: quantos dias, em média, o dinheiro leva para entrar depois da venda.",
  delinquency:
    "Pontualidade de pagamento dos clientes: compara a data de baixa do título com o vencimento. O recorte é consolidado — soma as duas filiais.",
  delinquencyAging:
    "Clientes com maior taxa de inadimplência no período: percentual de títulos pagos em atraso sobre o total de títulos do cliente (não o volume absoluto).",
  delinquencyCustomers:
    "Ranking de clientes pelo valor pago em atraso no período. Abra a linha para conferir título a título.",
  costCenters:
    "Despesa apropriada por centro de custo, a partir das notas de entrada. Use os filtros para isolar um centro ou um fornecedor.",
  excludeMpProducts:
    "Remove lançamentos cujo tipo de produto é MP (matéria-prima), para enxergar despesas fora de suprimentos.",
  costCenterSeries:
    "Despesa apropriada mês a mês nos últimos 12 meses, com os filtros da tela. Clique na coluna do mês para abrir o detalhamento com KPIs, rankings e cada lançamento.",
  costCenterEntries:
    "Cada linha é um item de nota de entrada com centro de custo apropriado. Abra a linha para ver pedido, conta contábil e rateio.",
  indicators:
    "Nota IDD do departamento Financeiro e IGD da Delpi, publicados no Indicadores estratégicos. A nota pondera cada indicador pelo peso definido na competência.",
  idd: "Índice de desempenho do departamento: média ponderada dos indicadores do Financeiro na competência.",
  igd: "Índice global da Delpi: consolida o IDD de todos os departamentos.",
  branch:
    "Filial usada na consulta (Santa Catarina ou Espírito Santo). O consolidado soma as duas e exige permissão de ambas.",
  period: "Recorte de datas da consulta. O fim é inclusivo na tela; a api-delpi usa limite exclusivo por mês de referência.",
  export: "Baixa o recorte atual em Excel, com os mesmos filtros aplicados na tela.",
  billingExtract:
    "Excel com cada nota de saída e devolução que entra na ROL do período — a mesma base do KPI, para conferência. Não são títulos de cobrança (SE1).",
} as const;
