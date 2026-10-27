/** PT-BR copy for the market intelligence page (PROC-0076 R4). */

export const MARKET_INTELLIGENCE_CONTENT = {
  title: "Inteligência de Mercado",
  eyebrow: "Portal Suprimentos",
  description:
    "Indicadores históricos de mercado de fontes autorizadas — " +
    "metais, câmbio oficial (PTAX) e indicadores industriais " +
    "(IBGE/Comex). Cada perspectiva mostra somente seus próprios " +
    "instrumentos, unidades e metodologia.",
  backToHome: "Início",
  reloadLabel: "Atualizar",

  perspectives: {
    switcherAriaLabel: "Perspectiva de dados",
    metals: "Metais",
    fx: "Câmbio",
    indicators: "Indicadores",
    metalsHint:
      "Cotações históricas dos seis metais industriais do catálogo, " +
      "em unidade nativa (US$/t). Somente fontes com direitos de " +
      "exibição homologados exibem valores.",
    indicatorsHint:
      "IPP do IBGE (Metalurgia) e importações Comex Stat por NCM " +
      "homologada — índices e valores médios, nunca cotação de metal.",
    fxHint: "Cotação PTAX de fechamento divulgada pelo Banco Central.",
  },

  filters: {
    instrumentLabel: "Instrumento",
    currencyLabel: "Moeda",
    granularityLabel: "Granularidade",
    fxKindLabel: "Tipo de PTAX",
    fromLabel: "De",
    toLabel: "Até",
    fxKindSell: "Venda (fechamento)",
    fxKindBuy: "Compra (fechamento)",
    granularityDay: "Dia",
    granularityWeek: "Semana",
    granularityMonth: "Mês",
    granularityYear: "Ano",
    indicatorLabel: "Indicador",
    indicatorIpp: "IPP (IBGE)",
    indicatorComex: "Comex (NCM)",
    seriesLabel: "Série",
    ncmLabel: "NCM",
  },

  kpis: {
    latestValueTitle: "Último valor",
    latestValueHint:
      "Observação mais recente dentro do período filtrado, na unidade " +
      "nativa da série.",
    latestReferenceTitle: "Última referência",
    latestReferenceHint:
      "Observação mais recente do instrumento no período filtrado, " +
      "na unidade nativa da série.",
    latestRateTitle: "Última PTAX",
    latestRateHint:
      "Boletim de fechamento mais recente no período, divulgado pelo " +
      "Banco Central do Brasil.",
    latestUnitValueTitle: "Último valor médio",
    latestUnitValueHint:
      "Valor médio de importação (FOB ÷ peso líquido) do último mês " +
      "com dados, em US$/t.",
    averageTitle: "Média do período",
    averageHint:
      "Média aritmética das observações válidas do período (método " +
      "versionado pela API).",
    variationTitle: "Variação do período",
    variationHint:
      "Variação percentual entre a primeira e a última observação válida.",
    minTitle: "Menor variação",
    minHint: "Menor variação mensal observada no período.",
    maxTitle: "Maior variação",
    maxHint: "Maior variação mensal observada no período.",
    minValueTitle: "Menor valor",
    minValueHint: "Menor observação válida da série no período.",
    maxValueTitle: "Maior valor",
    maxValueHint: "Maior observação válida da série no período.",
    fobTotalTitle: "FOB total",
    fobTotalHint: "Soma do valor FOB (US$) dos meses com observação.",
    weightTotalTitle: "Peso líquido total",
    weightTotalHint: "Soma do peso líquido (t) dos meses com observação.",
    observationsTitle: "Competências",
    observationsHint:
      "Meses com observação dentro do período esperado — lacunas não " +
      "são preenchidas artificialmente.",
    coverageTitle: "Cobertura",
    coverageHint:
      "Fração do período esperado com observações válidas (método " +
      "coverage_vs_expected/v1).",
    unavailable: "—",
  },

  panel: {
    viewSwitcherAriaLabel: "Modo de visualização",
    chartMode: "Gráfico",
    tableMode: "Tabela",
    compareMode: "Comparação",
    compareDisabledHint:
      "Comparação indisponível: as séries disponíveis têm unidades ou " +
      "granularidades incompatíveis (índice, %, US$/t, R$/US$).",
    compareNeedTwoSeries:
      "Comparação indisponível: selecione pelo menos dois instrumentos " +
      "com dados autorizados e unidade compatível.",
    loading: "Carregando série…",
    emptyTitle: "Sem dados no período",
    emptyMessage:
      "Não há observações para a série e o período selecionados. " +
      "Ajuste os filtros ou aguarde a próxima ingestão.",
    typeLabel: "Tipo do gráfico",
    seriesColorsLabel: "Cores da série",
    seriesColorsPanelTitle: "Cor da série",
    seriesColorsEmpty: "Sem preferências de cor",
    seriesColorsTriggerAria: "Abrir cores da série",
    seriesColorsReset: "Restaurar cor padrão",
    missingPeriodsNote: (periods: string[]) =>
      `Competências sem observação no período: ${periods.join(", ")}.`,
    missingPeriodsExplanation:
      "Ausência legítima: competência ainda não divulgada pela fonte ou " +
      "fora do histórico coletado — nunca exibida como zero.",
    methodologyLabel: "Metodologia",
    configPreviewLabel: "Estrutura prevista",
    nextStepsLabel: "Próximos passos",
  },

  /** Context cards shown when a perspective has no observations — real
   * feed/meta evidence, never placeholder data (R5.S2). */
  statusCards: {
    sourceStatusTitle: "Status da fonte",
    sourceStatusHint:
      "Estado reportado pelo serviço de dados de mercado para a série " +
      "consultada.",
    lastCollectionTitle: "Última coleta",
    lastCollectionHint:
      "Data/hora da última ingestão bem-sucedida registrada para esta " +
      "fonte.",
    latestObservationTitle: "Última observação",
    latestObservationHint:
      "Data da observação mais recente persistida desta fonte.",
    periodTitle: "Período consultado",
    periodHint: "Recorte de datas e frequência selecionados nos filtros.",
    seriesTitle: "Série",
    seriesHint: "Instrumento ou série selecionado nesta consulta.",
    emptyValue: "—",
  },

  /** Quote-basis labels emitted by the catalog — shown as context on
   * instrument cards and KPI lines (R5.S2). */
  quoteBasis: {
    comex_daily_close: "Fechamento COMEX",
    lme_daily_close: "Fechamento LME",
    spot_daily_close: "Fechamento spot",
    daily_close: "Fechamento diário",
    monthly_average: "Média mensal da fonte",
  } as Record<string, string>,

  summary: {
    sectionTitle: "Resumo do período",
    lastQuoteTitle: "Última cotação",
    lastQuoteHint:
      "Valor mais recente dentro do período filtrado, na moeda selecionada.",
    averageTitle: "Média do período",
    averageHint:
      "Média aritmética das observações válidas do período. " +
      "Meses sem câmbio não entram na média em BRL.",
    variationTitle: "Variação do período",
    variationHint:
      "Variação percentual entre a primeira e a última observação válida.",
    fxReferenceTitle: "Dólar de referência (PTAX)",
    fxReferenceHint:
      "Cotação PTAX de fechamento mais recente no período, divulgada pelo " +
      "Banco Central do Brasil.",
    validObservations: "observações válidas",
    unavailable: "—",
  },

  chart: {
    sectionTitle: "Evolução da cotação",
    sectionHint:
      "Série histórica na granularidade selecionada. Pontos sem dado " +
      "permanecem vazios — nunca são interpolados nem exibidos como zero.",
    loading: "Carregando série…",
    emptyTitle: "Sem dados no período",
    emptyMessage:
      "Não há observações para o instrumento e o período selecionados. " +
      "Ajuste os filtros ou aguarde a próxima ingestão.",
    typeLabel: "Tipo do gráfico",
    seriesColorsLabel: "Cores da série",
    seriesColorsPanelTitle: "Cor da série",
    seriesColorsEmpty: "Sem preferências de cor",
    seriesColorsTriggerAria: "Abrir cores da série",
    seriesColorsReset: "Restaurar cor padrão",
  },

  table: {
    sectionTitle: "Médias mensais",
    sectionHint:
      "Alternativa tabular acessível ao gráfico. Linhas sem dados são " +
      "exibidas explicitamente como ausentes.",
    loading: "Carregando médias…",
    emptyTitle: "Sem médias no período",
    emptyMessage: "Não há observações mensais para o período selecionado.",
    periodColumn: "Mês",
    averageColumn: "Média",
    nativeAverageColumn: "Média nativa (USD)",
    fxRateColumn: "PTAX do mês",
    observationsColumn: "Observações",
    coverageColumn: "Cobertura",
    coverageLabels: {
      ok: "Completa",
      partial: "Parcial",
      fx_missing: "Sem câmbio",
      no_data: "Sem dados",
    } as Record<string, string>,
  },

  modules: {
    importsTitle: "Importações — Comex Stat (MDIC)",
    importsHint:
      "Valor FOB, peso líquido e valor médio de importação em US$/t " +
      "por NCM homologada. Não é cotação internacional de metal.",
    importsNcmLabel: "NCM",
    importsNcmHint:
      "Somente NCMs homologadas por Compras aparecem para consulta.",
    importsPeriodColumn: "Período",
    importsFobColumn: "Valor FOB (US$)",
    importsWeightColumn: "Peso líquido (t)",
    importsUnitColumn: "Valor médio (US$/t)",
    importsRowsColumn: "Registros",
    ippTitle: "Preços Industriais — IPP (IBGE)",
    ippHint:
      "Índice de Preços ao Produtor da atividade Metalurgia. É um " +
      "índice/variação — não é cotação de metal nem valor monetário.",
    ippSeriesLabel: "Série IPP",
    ippPeriodColumn: "Período",
    ippValueColumn: "Valor",
    fxTitle: "Câmbio — PTAX (Banco Central)",
    fxHint:
      "Cotação PTAX oficial de fechamento. Dias sem boletim ficam " +
      "ausentes — nunca são preenchidos artificialmente.",
    fxKindSelectorLabel: "Tipo de boletim",
    fxPeriodColumn: "Período",
    fxValueColumn: "PTAX (R$/US$)",
  },

  metals: {
    sectionTitle: "Histórico de metais",
    sectionHint:
      "Instrumentos industriais do catálogo homologado. Selecione um " +
      "ou mais metais — a seleção prepara a visualização e a " +
      "comparação, mas nunca concede acesso a cotações protegidas.",
    cardsLabel: "Instrumentos",
    pendingLabel: "Fonte pendente",
    selectedLabel: "Selecionado",
    pendingSource:
      "Aguardando observações de fonte homologada — os instrumentos " +
      "selecionados existem no catálogo, mas a fonte ainda não tem " +
      "direitos de exibição aprovados. Nenhum valor é exibido.",
    emptySelectionTitle: "Selecione um ou mais metais",
    emptySelectionMessage:
      "Marque os instrumentos acima para montar o histórico. A " +
      "seleção persiste na URL — o link restaura a mesma visão.",
    unavailableSelectionLabel:
      "Selecionados sem exibição autorizada no momento",
    latestRefLabel: (date: string) => `Ref.: ${date}`,
    periodColumn: "Período",
    frequencyUnsupported:
      "frequência ainda não suportada pela série selecionada",
    unitNote: (unit: string) =>
      `Valores em unidade nativa (${unit}) — nunca convertidos ` +
      "implicitamente nem misturados com índices ou câmbio.",
    subtitle: (labels: string[]) =>
      `Instrumentos selecionados: ${labels.join(", ")}`,
  },

  states: {
    loading: "Carregando inteligência de mercado…",
    moduleUnavailable:
      "Este indicador está indisponível no momento — a fonte não foi " +
      "ativada ou os direitos de exibição estão em revisão.",
    comexConfigPendingTitle: "Comex — configuração pendente",
    comexConfigPending:
      "Nenhuma NCM homologada por Compras está disponível para consulta. " +
      "Quando a homologação for concluída e a fonte MDIC estiver ativa, " +
      "as importações aparecem aqui.",
    comexNextSteps:
      "Próximo passo: homologar a lista de NCMs de interesse com " +
      "Compras e confirmar a fonte MDIC Comex Stat ativa. A estrutura " +
      "abaixo mostra os indicadores que serão preenchidos — nenhum " +
      "valor é simulado.",
    providerUnavailable:
      "Fonte temporariamente indisponível: a última coleta falhou no " +
      "provedor oficial. O serviço tenta novamente no próximo ciclo — " +
      "nenhum valor sintético é exibido.",
    feedFailed:
      "A última coleta desta fonte falhou. Os dados históricos " +
      "persistidos, quando existirem, seguem disponíveis.",
    feedDisabled:
      "Coleta desta fonte desativada no momento — os dados aparecem " +
      "quando a ingestão for reativada.",
    feedNotCollected:
      "Nenhuma coleta concluída desta fonte até o momento — os dados " +
      "aparecem após a primeira ingestão bem-sucedida.",
    windowEmpty:
      "Sem observações dentro do período filtrado — amplie o recorte " +
      "ou aguarde a próxima publicação da fonte.",
    granularityNotSupported:
      "Este instrumento não possui observações na frequência " +
      "selecionada — a fonte dele publica em outra periodicidade.",
    sourceUsePending:
      "Fonte ainda não homologada para exibição deste instrumento.",
    partialNote:
      "Dados parciais: parte do período não possui observações ou " +
      "câmbio correspondente.",
    staleNote:
      "Dados possivelmente desatualizados: a fonte está atrasada em " +
      "relação ao seu ciclo de publicação.",
    staleEvidence: (latest: string | null, expected: string) =>
      `Última observação disponível: ${latest ?? "—"}; esperada até: ${expected}.`,
    fxMissingNote: "Conversão indisponível: não há PTAX para o mês de referência.",
    noSelectableInstruments:
      "Nenhum instrumento está disponível para consulta no momento — " +
      "os direitos de exibição das fontes estão em revisão.",
    sourceLabel: "Fonte",
    asOfLabel: "Última ingestão bem-sucedida",
    methodLabel: "Método",
    attributionLabel: "Atribuição",
  },

  errors: {
    generic:
      "Não foi possível carregar os indicadores. Tente novamente em instantes.",
    unavailable:
      "O serviço de dados de mercado está indisponível no momento.",
    timeout: "O serviço de dados de mercado demorou demais para responder.",
    rateLimited:
      "Limite de requisições atingido. Aguarde alguns instantes e tente de novo.",
    invalidFilters:
      "Filtros inválidos para a série selecionada. Revise granularidade e período.",
    notFound: "Série não encontrada no catálogo de fontes autorizadas.",
    unauthorized: "Sua sessão expirou. Entre novamente para continuar.",
    forbidden:
      "Você não possui acesso à inteligência de mercado de Suprimentos.",
    sourceNotApproved:
      "Os dados desta fonte estão temporariamente indisponíveis " +
      "enquanto os direitos de exibição passam por revisão.",
  },
} as const;

export type MarketIntelligenceContent = typeof MARKET_INTELLIGENCE_CONTENT;

/** Map BFF error codes/statuses to user-facing copy. */
export function mapMarketIntelligenceError(error: unknown): string {
  const status =
    error && typeof error === "object" && "status" in error
      ? Number((error as { status?: number }).status)
      : undefined;
  const code =
    error && typeof error === "object" && "code" in error
      ? String((error as { code?: string }).code ?? "")
      : "";
  if (status === 401) return MARKET_INTELLIGENCE_CONTENT.errors.unauthorized;
  if (status === 403) return MARKET_INTELLIGENCE_CONTENT.errors.forbidden;
  if (code === "source_use_not_approved")
    return MARKET_INTELLIGENCE_CONTENT.errors.sourceNotApproved;
  if (status === 429 || code === "rate_limited")
    return MARKET_INTELLIGENCE_CONTENT.errors.rateLimited;
  if (status === 404 || code === "not_found")
    return MARKET_INTELLIGENCE_CONTENT.errors.notFound;
  if (status === 422 || code === "unprocessable")
    return MARKET_INTELLIGENCE_CONTENT.errors.invalidFilters;
  if (status === 504 || code === "gateway_timeout")
    return MARKET_INTELLIGENCE_CONTENT.errors.timeout;
  if (status === 503 || status === 502 || code === "external_data_unavailable")
    return MARKET_INTELLIGENCE_CONTENT.errors.unavailable;
  return MARKET_INTELLIGENCE_CONTENT.errors.generic;
}
