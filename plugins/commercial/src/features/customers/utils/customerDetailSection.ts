export type CustomerDetailSection =
  | "resumo"
  | "pedidos"
  | "historico"
  | "oportunidades"
  | "contatos";

/** Valores canônicos + aliases legados (ex.: faturamento → historico). */
const SECTION_ALIASES: Record<string, CustomerDetailSection> = {
  resumo: "resumo",
  overview: "resumo",
  "visao-geral": "resumo",
  pedidos: "pedidos",
  faturamento: "historico",
  historico: "historico",
  oportunidades: "oportunidades",
  contatos: "contatos",
  /** Alias legado — aba removida; cai na visão geral. */
  checkups: "resumo",
};

export const CUSTOMER_DETAIL_SECTION_ORDER: readonly CustomerDetailSection[] = [
  "resumo",
  "pedidos",
  "historico",
  "oportunidades",
  "contatos",
] as const;

export function parseCustomerDetailSection(
  search: string | undefined,
): CustomerDetailSection {
  if (!search) return "resumo";
  const params = new URLSearchParams(
    search.startsWith("?") ? search.slice(1) : search,
  );
  const value = (params.get("secao") || params.get("section") || "").trim().toLowerCase();
  return SECTION_ALIASES[value] ?? "resumo";
}

export function buildCustomerDetailSearch(
  section: CustomerDetailSection,
  currentSearch?: string,
): string {
  const params = new URLSearchParams(
    currentSearch
      ? currentSearch.startsWith("?")
        ? currentSearch.slice(1)
        : currentSearch
      : "",
  );
  if (section === "resumo") {
    params.delete("secao");
    params.delete("section");
  } else {
    params.set("secao", section);
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function isHistorySection(section: CustomerDetailSection): boolean {
  return section === "historico";
}
