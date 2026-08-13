export type CustomerDetailSection =
  | "resumo"
  | "pedidos"
  | "historico"
  | "oportunidades"
  | "contatos"
  | "atividades";

/** Valores canônicos + aliases legados (ex.: faturamento → historico). */
const SECTION_ALIASES: Record<string, CustomerDetailSection> = {
  resumo: "resumo",
  overview: "resumo",
  "visao-geral": "resumo",
  pedidos: "pedidos",
  faturamento: "historico",
  historico: "historico",
  oportunidades: "oportunidades",
  atividades: "atividades",
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
  "atividades",
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

export function resolveCustomerDetailFetchPolicy(options: {
  section: CustomerDetailSection;
  hasCustomer: boolean;
  canViewWorklist: boolean;
}): { billing: boolean; activities: boolean } {
  const { section, hasCustomer, canViewWorklist } = options;
  return {
    billing: hasCustomer && section === "historico",
    activities:
      hasCustomer &&
      canViewWorklist &&
      (section === "resumo" || section === "atividades"),
  };
}

export function customerDetailTabId(section: CustomerDetailSection): string {
  return `customer-tab-${section}`;
}

export function customerDetailPanelId(section: CustomerDetailSection): string {
  return `customer-panel-${section}`;
}
