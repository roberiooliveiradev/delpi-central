export const DP_HELP_TOOLTIPS = {
  filters: {
    dateStart:
      "Início do período analisado. KPIs, gráficos e tabelas consideram apontamentos ou OPs com data dentro do intervalo.",
    dateEnd:
      "Fim do período analisado. Deve ser igual ou posterior à data inicial.",
    branch:
      "Filial TOTVS (01 ou 02). Consolidado calcula a média entre filiais nos indicadores agregados.",
  },
  home: {
    directLabor:
      "Percentual da mão de obra direta sobre a receita operacional líquida (ROL) no período.",
    productionCost:
      "Percentual do custo total de produção sobre a ROL no período.",
    depreciation:
      "Percentual da depreciação fabril sobre a ROL no período.",
    oee: "Média de eficiência dos apontamentos válidos (0–199%) na view fabril compartilhada.",
    otd: "Percentual de ordens de produção finalizadas dentro do prazo previsto.",
    comparisonChart:
      "Comparativo dos cinco indicadores principais do painel no período e filial selecionados.",
    oeeEvolution:
      "Série temporal do OEE (%). Clique em um ponto para restringir o período aos filtros de data.",
    otdEvolution:
      "Série temporal do OTD (%). Clique em um ponto para restringir o período aos filtros de data.",
  },
  oee: {
    kpiOee:
      "Média simples da eficiência (EFICIENCIA_PERCENTUAL) dos apontamentos na faixa 0–199%. Com filtros de OP, operador, CT, tipo ou faixa, reflete o subconjunto filtrado.",
    kpiAppointments:
      "Total de apontamentos listáveis no período, incluindo registros fora da faixa (Verificar) e eficiência baixa.",
    kpiValid:
      "Quantidade de apontamentos válidos que compõem o indicador de OEE e a média exibida no KPI principal.",
    chartEvolution:
      "Evolução do OEE no tempo conforme a granularidade escolhida (dia, semana ou mês).",
    filters: {
      productionOrder:
        "Filtra por ordem de produção (OP). Permite múltipla seleção.",
      operator:
        "Filtra por código do operador. Permite múltipla seleção.",
      workCenter:
        "Filtra por centro de trabalho (CT). Permite múltipla seleção.",
      productType:
        "PA = produto acabado; PI = produto intermediário. Restringe apontamentos e recalcula KPIs do resumo quando aplicado.",
      efficiencyBands:
        "Filtra apontamentos por faixa: na faixa (≥ 50%), eficiência baixa (< 50%) ou fora da faixa (0–199%).",
    },
    table: {
      section:
        "Apontamentos de produção do período. Clique na linha para abrir roteiro, estrutura e análise de tempos.",
      productionDate: "Data de produção do apontamento (SH6010).",
      startTime: "Horário de início do apontamento.",
      endTime: "Horário de término do apontamento.",
      producedQty: "Quantidade produzida registrada no apontamento.",
      branch: "Filial TOTVS do apontamento.",
      productionOrder: "Número da ordem de produção (OP).",
      productDescription: "Descrição do produto fabricado na OP.",
      workCenter: "Centro de trabalho (CT) onde o apontamento foi realizado.",
      operatorCode: "Código do operador responsável pelo apontamento.",
      oeePct:
        "Eficiência percentual do apontamento. Valores fora de 0–199% ou abaixo de 50% recebem destaque na coluna Status.",
      status:
        "OK = na faixa; Eficiência baixa = válido e < 50%; Verificar = fora da faixa 0–199%.",
    },
  },
  otd: {
    kpiOtd: "Percentual de OPs finalizadas no prazo em relação ao total de OPs encerradas no período.",
    kpiOnTime: "Quantidade de ordens finalizadas até a data prevista (due date).",
    kpiLate: "Quantidade de ordens finalizadas após a data prevista.",
    chartEvolution: "Evolução do OTD no tempo conforme a granularidade escolhida.",
    filters: {
      status: "Restringe a listagem a OPs no prazo, atrasadas ou exibe todas.",
    },
    table: {
      section: "Ordens de produção finalizadas no período. Clique na linha para ver detalhes e OPs intermediárias.",
      status: "No prazo ou atrasada conforme comparação entre data de conclusão e data prevista.",
      branch: "Filial TOTVS da ordem.",
      productionOrder: "Identificador da ordem de produção.",
      orderNumber: "Número da OP no Protheus.",
      orderItem: "Item da ordem de produção.",
      productCode: "Código do produto fabricado.",
      productDescription: "Descrição do produto da OP.",
      dueDate: "Data prevista para conclusão da ordem.",
      finishDate: "Data em que a ordem foi efetivamente finalizada.",
      daysDiff: "Diferença em dias entre a data de finalização e a data prevista.",
      producedQty: "Quantidade produzida na ordem.",
      otdStatus: "Situação calculada de entrega no prazo (OTD).",
    },
  },
} as const;
