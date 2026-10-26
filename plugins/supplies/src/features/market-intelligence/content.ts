/** PT-BR copy for the market intelligence page (PROC-0076). */

export const MARKET_INTELLIGENCE_CONTENT = {
  title: "Inteligência de Mercado",
  eyebrow: "Portal Suprimentos",
  description:
    "Cotações históricas de metais e câmbio de fontes autorizadas. " +
    "Valores em USD são nativos da fonte; a conversão para BRL usa a " +
    "média PTAX do mês de referência.",
  backToHome: "Início",
  reloadLabel: "Atualizar",

  filters: {
    instrumentLabel: "Instrumento",
    currencyLabel: "Moeda",
    granularityLabel: "Granularidade",
    fxKindLabel: "Tipo de PTAX",
    fromLabel: "De",
    toLabel: "Até",
    fxKindSell: "Venda (fechamento)",
    fxKindBuy: "Compra (fechamento)",
    granularityDay: "Diário",
    granularityMonth: "Mensal",
    granularityYear: "Anual",
  },

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

  states: {
    loading: "Carregando inteligência de mercado…",
    partialNote:
      "Dados parciais: parte do período não possui observações ou " +
      "câmbio correspondente.",
    staleNote:
      "Dados possivelmente desatualizados: a fonte está atrasada em " +
      "relação ao seu ciclo de publicação.",
    staleEvidence: (latest: string | null, expected: string) =>
      `Última observação disponível: ${latest ?? "—"}; esperada até: ${expected}.`,
    fxMissingNote: "Conversão indisponível: não há PTAX para o mês de referência.",
    sourceLabel: "Fonte",
    asOfLabel: "Última ingestão bem-sucedida",
    methodLabel: "Método",
    attributionLabel: "Atribuição",
  },

  errors: {
    generic:
      "Não foi possível carregar as cotações. Tente novamente em instantes.",
    unavailable:
      "O serviço de dados de mercado está indisponível no momento.",
    timeout: "O serviço de dados de mercado demorou demais para responder.",
    rateLimited:
      "Limite de requisições atingido. Aguarde alguns instantes e tente de novo.",
    invalidFilters:
      "Filtros inválidos para o instrumento selecionado. Revise moeda, " +
      "granularidade e período.",
    notFound: "Instrumento não encontrado no catálogo de fontes autorizadas.",
    unauthorized: "Sua sessão expirou. Entre novamente para continuar.",
    forbidden:
      "Você não possui acesso à inteligência de mercado de Suprimentos.",
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
