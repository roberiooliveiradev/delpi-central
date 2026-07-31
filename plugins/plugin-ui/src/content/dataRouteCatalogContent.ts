/** Microcopy do catálogo Fontes (plugin-ui). */
export const DATA_ROUTE_CATALOG_CONTENT = {
  searchPlaceholder: "Descreva o dado ou busque pelo nome…",
  suggestionsBadge: "Sugestão",
  suggestionsLoading: "Buscando fontes…",
  suggestionsEmpty:
    "Nenhuma sugestão para essa frase. Tente termos como «estoque», «OEE», «refugo».",
  suggestionsUnavailable:
    "Sugestões indisponíveis no momento. Use a busca por nome ou tente de novo em instantes.",
  suggestionsTitlePrefix: "Sugestões para",
} as const;

export function formatDataRouteSuggestionsTitle(query: string): string {
  const trimmed = String(query || "").trim();
  if (!trimmed) return "Sugestões";
  return `${DATA_ROUTE_CATALOG_CONTENT.suggestionsTitlePrefix} «${trimmed}»`;
}
