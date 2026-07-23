export const QUALITY_HELP_TOOLTIPS = {
  actions: {
    pageSubtitle:
      "Indicadores de qualidade: PPM interno/externo, kaizens, auditorias 5S e não conformidades.",
    refresh: "Recarrega PPM, kaizens e auditorias com os filtros atuais.",
  },
  filters: {
    competence:
      "Mês de referência (aaaa-mm). Ao selecionar, ajusta o período para o mês inteiro — ou até hoje, no mês corrente. Fica vazio quando o período abrange mais de um mês.",
    dateStart: "Início do período para PPM, kaizens e auditorias 5S.",
    dateEnd: "Fim do período. Deve ser igual ou posterior à data inicial.",
    branch:
      "Unidade TOTVS. Vazio = todas; múltiplas unidades restringem o recorte dos indicadores.",
    ppmProductScope:
      "Recorte de PPM por família: filtra devoluções (QI2_ITEM) por prefixo — plugues 9048, componentes 9026. A produção do denominador permanece geral.",
    nonconformityType:
      "Interna (tipo 1) ou externa (cliente/fornecedor). Vazio = todos os tipos.",
    nonconformityStatus:
      "Busca aproximada por situação: aceita parte do rótulo (ex.: «procede», «análise») ou do código TOTVS.",
    nonconformityItem:
      "Busca aproximada no código do produto (QI2_ITEM). Ex.: «9048» encontra itens que contenham esse trecho.",
    nonconformityDescription:
      "Busca aproximada na descrição resumida da NC (QI2_DESCR), sem exigir texto idêntico.",
  },
  kpis: {
    ppmInternal:
      "Parts Per Million interno: devoluções internas por milhão de unidades produzidas no período.",
    ppmExternal:
      "PPM externo: devoluções de clientes por milhão de unidades faturadas.",
    ppmInternalPlugs:
      "PPM interno de plugues: devoluções internas de produtos 9048* sobre a produção total do período.",
    ppmExternalPlugs:
      "PPM externo de plugues: devoluções externas de produtos 9048* sobre a produção total do período.",
    ppmInternalComponents:
      "PPM interno de componentes: devoluções internas de produtos 9026* sobre a produção total do período.",
    ppmExternalComponents:
      "PPM externo de componentes: devoluções externas de produtos 9026* sobre a produção total do período.",
    kaizenOpen: "Quantidade de kaizens com status Recebido (fila de sugestões) no recorte.",
    kaizenClosed: "Kaizens concluídos no período filtrado.",
    kaizenTotal: "Total de kaizens registrados no período conforme filtros aplicados.",
    kaizenIdeas:
      "Quantidade de kaizens com status Aprovado ou Implantado no período, pela data de aprovação no comitê (ou data de implantação, se a aprovação não estiver cadastrada). Meta do indicador Ideias Aprovadas para Kaizen/mês (Indicadores Estratégicos).",
    kaizenFinancialGains:
      "Ganhos financeiros do kaizen no período: soma de daily_savings × dias ativos apenas de melhorias com status Implantado. Status Aprovado conta na quantidade, mas não nos ganhos. Meta do indicador Ganhos Financeiros Kaizen/mês (Indicadores Estratégicos).",
    kaizenSavings:
      "Mesmo valor dos ganhos financeiros do kaizen — economia acumulada no período filtrado.",
    audit5sScore: "Nota média das auditorias 5S realizadas no período.",
    audit5sCount: "Quantidade de auditorias 5S registradas no recorte.",
    nonconformities: "Total de não conformidades abertas ou registradas no período.",
    ppmDetail: "PPM calculado com base em unidades devolvidas e produzidas/faturadas.",
    ppmReturned: "Quantidade total de unidades devolvidas no período.",
  },
  charts: {
    ppmEvolution: "Evolução temporal do PPM conforme granularidade selecionada.",
    kaizenByStatus: "Distribuição de kaizens por status no período.",
    kaizenByPeriod:
      "Contagem de ideias aprovadas/implantadas por período, usando a data de aprovação no comitê (ou implantação se a aprovação não estiver cadastrada) — a mesma âncora do KPI Ideias aprovadas.",
    audit5sEvolution: "Evolução das notas de auditoria 5S ao longo do tempo.",
  },
  pagination: {
    info: "Paginação: busca, ordenação e tamanho da página são aplicados na consulta ou na página atual.",
    pageSize: "Define quantos registros são exibidos por página (10, 20, 50 ou 100).",
    jump: "Digite o número da página e pressione Enter ou saia do campo.",
    jumpEmpty: "Informe um número de página.",
    jumpInvalid: "Use apenas números inteiros.",
    jumpBelowMin: "A página mínima é 1.",
    previous: "Volta uma página mantendo busca, ordenação e tamanho da lista.",
    next: "Avança uma página mantendo busca, ordenação e tamanho da lista.",
  },
  table: {
    section: "Listagem do período filtrado. Clique na linha para ver o detalhe quando disponível.",
    search: "Filtra os registros visíveis por texto nas colunas principais.",
    branch: "Unidade TOTVS do registro.",
  },
} as const;
