/** Textos PT-BR da Auditoria de Consumo (GLPI #1353).
 *  Códigos internos do ERP ficam fora da prosa — o rótulo explica o fenômeno. */

export const CONSUMPTION_AUDIT_CONTENT = {
  title: "Auditoria de Consumo",
  eyebrow: "Portal Suprimentos",
  description:
    "Consulta analítica de uma ordem de produção: o que a estrutura previa, o que foi empenhado e o que o ERP registrou como consumo — com as evidências de execução de cada operação. Dados calculados pelo servidor; o Portal não recalcula.",

  // ——— Consulta ———
  queryTitle: "Consultar ordem de produção",
  queryHint:
    "Informe a chave completa da OP (11 posições: número + item + sequência) e a filial. A consulta fica na URL — F5 e compartilhamento restauram o mesmo resultado.",
  unitLabel: "Filial",
  opLabel: "Ordem de produção",
  opPlaceholder: "Ex.: 24884201006",
  opInvalid:
    "A OP deve ter 11 posições alfanuméricas (número + item + sequência, sem traços).",
  unitInvalid: "Selecione uma filial antes de consultar.",
  consultAction: "Consultar",
  consultAgainAction: "Nova consulta",
  refreshAction: "Atualizar",
  updatedAtLabel: (time: string) => `Consultado às ${time}`,
  loading: "Consultando a ordem no ERP…",

  // ——— Busca automática (F2) ———
  searchTitle: "Pesquisar ordens de produção",
  searchHint:
    "Digite parte do número da OP, ou use os filtros para localizar ordens por produto, período, situação, centro de trabalho e operação. A pesquisa é automática — não é preciso confirmar.",
  searchPlaceholder: "Digite parte da OP ou use os filtros abaixo…",
  searchMinChars: (min: number) => `Digite ao menos ${min} caracteres ou combine os filtros.`,
  searchLoading: "Pesquisando…",
  searchEmpty: "Nenhuma ordem encontrada com estes critérios.",
  searchResultsTitle: "Resultados",
  searchResultsSubtitle: (total: number) =>
    `${total} ordem(ns) encontrada(s) — selecione uma linha para abrir a auditoria completa.`,
  searchPageOf: (page: number, totalPages: number) =>
    `Página ${page} de ${totalPages}`,
  searchPrevPage: "Anterior",
  searchNextPage: "Próxima",
  suggestionFor: (op: string, product: string) => `OP ${op} · ${product}`,

  // ——— Período rápido ———
  quickPeriodLabel: "Período rápido",
  quickPeriodHint:
    "Atalhos preenchem as datas inicial e final do filtro; o período usa o tipo de data escolhido (Emissão, Apontamento ou Encerramento).",
  clearPeriod: "Limpar período",
  filtersAriaLabel: "Pesquisa e filtros de ordens de produção",
  advancedFiltersTitle: "Filtros avançados",

  // ——— Filtros avançados (F3) ———
  filtersTitle: "Filtros de pesquisa",
  filtersHint:
    "Os filtros se combinam (interseção): período usa o tipo de data escolhido; produto aceita código ou descrição parcial.",
  dateTypeLabel: "Tipo de data",
  dateTypes: {
    emission: "Emissão",
    appointment: "Apontamento",
    finished: "Encerramento",
  } as Record<string, string>,
  periodStartLabel: "Data inicial",
  periodEndLabel: "Data final",
  productLabel: "Produto (código ou descrição)",
  productPlaceholder: "Ex.: CABO ou 50226108",
  statusFilterLabel: "Situação",
  statusAllLabel: "Todas",
  workCenterLabel: "Centro de trabalho",
  workCenterPlaceholder: "Ex.: CT-23",
  operationLabel: "Operação",
  operationPlaceholder: "Ex.: 01",
  clearFilters: "Limpar filtros",
  colOrder: "OP",
  colProduct: "Produto",
  colStatus: "Situação",
  colEmission: "Emissão",
  colFinished: "Encerramento",
  colPlanned: "Qtd. planejada",
  compareSelect: "Comparar",

  // ——— Comparação (F4) ———
  compareTitle: "Comparação de ordens",
  compareHint:
    "Selecione de 2 a 10 OPs na lista de resultados (todas da mesma filial). A comparação projeta cada OP separadamente — totais só somam componentes da mesma unidade de medida; diferenças não provam irregularidade.",
  compareAction: (count: number) => `Comparar ${count} OPs`,
  compareMinMax: "Selecione entre 2 e 10 ordens para comparar.",
  compareMaxReached: "Limite de 10 ordens selecionadas.",
  compareNotFound: "Sem dados para estas OPs nesta filial: ",
  compareLoading: "Comparando ordens…",
  compareClose: "Fechar comparação",
  compareColMetric: "Medida",
  compareTotalsTitle: "Totais por unidade de medida",
  compareComponentsTitle: "Componentes por operação",
  compareQualityTitle: "Qualidade das informações",
  compareNoUm: "Sem UM",
  metricTheoretical: "Estrutura teórica",
  metricCommitted: "Empenho original",
  metricOpen: "Saldo empenhado",
  metricDerived: "Consumo derivado",
  metricEligible: "Consumo classificado",

  // ——— Estados ———
  emptyTitle: "Informe uma ordem de produção",
  emptyMessage:
    "A auditoria mostra, para uma OP específica, estrutura prevista, empenhos, consumo registrado e evidências de execução por operação.",
  notFound:
    "Ordem de produção não encontrada nesta filial. Confira a chave completa (11 posições) e a filial.",
  forbidden:
    "Você não tem permissão para auditar consumo nesta filial. Peça o acesso canônico ao administrador.",
  error: "Não foi possível consultar a auditoria da ordem.",
  upstreamDown:
    "O serviço de dados de produção está indisponível no momento — tente novamente em instantes.",
  invalidResponse:
    "Resposta inválida do servidor — os dados não puderam ser interpretados.",
  retry: "Tentar novamente",

  // ——— Identificação ———
  orderTitle: "Ordem de produção",
  orderHint:
    "Identificação e quantidades da OP conforme registradas no ERP.",
  orderProduct: "Produto",
  orderProductType: "Tipo",
  orderPlannedQty: "Qtd. planejada",
  orderProducedQty: "Qtd. registrada",
  orderProducedBasis: "Base da produção",
  orderStatus: "Situação",
  orderEmission: "Emissão",
  orderPlannedStart: "Início previsto",
  orderDue: "Término previsto",
  orderFinishedAt: "Encerrada em",
  orderWarehouse: "Armazém",
  orderPriority: "Prioridade",
  orderType: "Tipo de OP",
  orderUnit: "UM",
  producedBasisStockReceipt: "Apontamento de produção no ERP",
  producedBasisUnknown: "Registrada no ERP",

  statusLabels: {
    N: "Em aberto",
    P: "Em produção",
    T: "Encerrada",
    C: "Cancelada",
  } as Record<string, string>,

  // ——— Operações ———
  operationsTitle: "Operações",
  operationsHint:
    "Cada operação da rota com seu centro de trabalho e as evidências de execução encontradas.",
  operationTitle: (op: string, wc: string) => `Operação ${op} · ${wc}`,
  operationNoComponents: "Nenhum componente previsto nesta operação.",
  executionStateTitle: "Execução",
  executionStates: {
    evidenced: "Apontada",
    pending: "Pendente",
    unknown: "Desconhecida",
  } as Record<string, string>,
  executionStateHints: {
    evidenced: "Existe apontamento registrado para a operação.",
    pending:
      "A operação tem programação, mas nenhum apontamento encontrado — não prova não-execução.",
    unknown: "Não há evidência suficiente para classificar a execução.",
  } as Record<string, string>,
  sh8Title: "Programação",
  sh8Absent: "Sem linha de programação para esta operação.",
  sh8Quantity: "Qtd. programada",
  sh8Window: (start: string, end: string) => `${start} → ${end}`,
  sh6Title: "Apontamentos",
  sh6Resource: "Recurso",
  sh6Reported: "Qtd. apontada",
  sh6Lost: "Qtd. perdida",
  sh6Window: "Período",
  hzaTitle: "Coletor",
  hzaStatus: "Status",
  hzaNoResource: "—",

  // ——— Materiais ———
  materialsTitle: "Materiais",
  materialsHint:
    "Componentes previstos pela estrutura na data de emissão da OP, com empenhos e consumo classificado.",
  colComponent: "Componente",
  colDescription: "Descrição",
  colUm: "UM",
  colTheoretical: "Teórico",
  colCommitment: "Empenho original",
  colOpenQty: "Saldo empenhado",
  colDerived: "Consumo derivado",
  colClassified: "Consumo classificado",
  colDiscrepancy: "Diferença",
  colClassification: "Situação",
  umNotComparableHint:
    "Unidades de medida diferentes não são comparáveis — cada quantidade vale dentro da sua UM.",

  classifications: {
    reconciled: "Conciliado",
    pending: "Pendente",
    requires_investigation: "Requer análise",
    partial: "Parcial",
    unknown: "Indeterminada",
  } as Record<string, string>,
  classificationHints: {
    reconciled: "Consumo classificado cobre o consumo derivado dos empenhos.",
    pending: "Sem consumo registrado até o momento — empenho ainda em aberto.",
    requires_investigation:
      "Diferença entre empenhado e consumido que não se explica sozinha — verifique as movimentações.",
    partial: "Só parte das evidências foi encontrada.",
    unknown: "Evidência insuficiente para classificar.",
  } as Record<string, string>,

  discrepancyHint:
    "Diferença calculada pelo servidor entre o consumo derivado dos empenhos e o classificado.",

  // ——— Movimentações ———
  movementsTitle: "Movimentações",
  movementsHint:
    "Registros de movimentação do componente nesta OP: os que compõem o consumo e os excluídos do cálculo.",
  movementsShow: "Ver movimentações",
  movementsHide: "Ocultar movimentações",
  movementsNone: "Nenhuma movimentação registrada para este componente.",
  movementsClassified: "Compõem o consumo",
  movementsExcluded: "Excluídas do cálculo",
  colDocument: "Documento",
  colIssueDate: "Data",
  colMovementKind: "Tipo",
  colDirection: "Sentido",
  colQuantity: "Quantidade",
  colWarehouse: "Armazém",
  colReason: "Motivo",
  reversedTag: "estornada",

  movementKinds: {
    production_consumption: "Consumo de produção",
    production_receipt: "Receita de produção",
    warehouse_transfer: "Transferência entre armazéns",
    inventory_adjustment_in: "Ajuste de inventário (entrada)",
    inventory_adjustment_out: "Ajuste de inventário (saída)",
    unclassified: "Não classificada",
  } as Record<string, string>,
  movementDirections: {
    inbound: "Entrada",
    outbound: "Saída",
  } as Record<string, string>,
  exclusionReasons: {
    not_raw_material_consumption: "Não é consumo de matéria-prima",
    labor_not_material: "Mão de obra — não é material",
    reversed_document: "Movimentação estornada",
    different_production_order: "Vinculada a outra OP",
    outside_order_window: "Fora da janela da OP",
  } as Record<string, string>,

  // ——— Movimentações sem empenho ———
  unmatchedTitle: "Registros sem empenho correspondente",
  unmatchedHint:
    "Movimentações da OP que não casam com nenhum empenho — ficam visíveis como evidência, fora da soma de matéria-prima.",

  // ——— OPs relacionadas ———
  relatedTitle: "Ordens relacionadas",
  relatedHint:
    "Outras OPs do mesmo número de ordem e vínculos comprovados por empenho de origem.",
  relatedRelationships: {
    same_order_number: "Mesmo número de ordem",
    parent_commitment_via_d4_oporig: "OP de origem do empenho",
  } as Record<string, string>,
  relatedConfidenceProven: "Comprovado",
  relatedOpenAction: "Abrir",

  // ——— Qualidade ———
  qualityTitle: "Qualidade das informações",
  qualityStatusComplete: "Completa",
  qualityStatusPartial: "Parcial",
  qualityPartialHint:
    "Parte das evidências está incompleta ou ambígua — os itens abaixo explicam o que falta. Nada aqui é acusação de irregularidade.",
  warningsTitle: "Pontos de atenção",
  warningLabels: {
    movements_without_commitment:
      "Existem movimentações sem empenho correspondente.",
    re0_tm999_ambiguity:
      "Uma transferência registrada de forma ambígua foi excluída do consumo — não entra na soma nem prova erro.",
    sh6_vs_sc2_quantity_mismatch:
      "A quantidade apontada difere da registrada na OP — os dois valores são mostrados separadamente.",
  } as Record<string, string>,
  unresolvedTitle: "Interpretações não resolvidas",
  unresolvedLabels: {
    automatic_issue_causality:
      "Não é possível afirmar, só pelos registros, quem disparou baixas automáticas.",
    re0_tm999_transfer_meaning:
      "O significado exato da movimentação de transferência não foi confirmado no ERP.",
    sh8_row_removal_semantics:
      "Ausência de linha de programação não prova execução nem não-execução.",
  } as Record<string, string>,

  // ——— Meta ———
  metaContract: (version: string) => `Contrato ${version}`,
  metaSource: (source: string) => `Gerado por ${source}`,
  toleranceHint:
    "Tolerância de conciliação definida pelo servidor para este recorte.",

  // ——— Ajuda ———
  helpSummary:
    "Auditoria de consumo: estrutura prevista × empenhos × consumo registrado por operação, com as evidências do ERP.",
} as const;
