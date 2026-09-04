export type OpportunityTableColumnItem = {
  key: string;
  label: string;
};

export const OPPORTUNITY_LIST_COLUMNS_STORAGE_KEY =
  "commercial:analytics-opportunities:table-columns:v1";
export const OPPORTUNITY_LIST_FONT_STORAGE_KEY =
  "commercial:analytics-opportunities:table-font-size:v1";

export const OPPORTUNITY_COLLABORATOR_COLUMNS_STORAGE_KEY =
  "commercial:analytics-opportunities-collaborator:table-columns:v1";
export const OPPORTUNITY_COLLABORATOR_FONT_STORAGE_KEY =
  "commercial:analytics-opportunities-collaborator:table-font-size:v1";

/** Catálogo completo da lista global (Visão Por oportunidade). */
export const OPPORTUNITY_LIST_COLUMN_CATALOG: readonly OpportunityTableColumnItem[] = [
  { key: "ov", label: "OV" },
  { key: "rev", label: "Rev." },
  { key: "customer", label: "Cliente" },
  { key: "seller", label: "Vendedor" },
  { key: "status", label: "Status" },
  { key: "stage", label: "Etapa" },
  { key: "date", label: "Data" },
  { key: "proposal-doc", label: "Proposta" },
] as const;

export const OPPORTUNITY_COLLABORATOR_COLUMN_CATALOG: readonly OpportunityTableColumnItem[] = [
  { key: "seller", label: "Vendedor" },
  { key: "open", label: "Abertas" },
  { key: "won", label: "Ganhas" },
  { key: "lost", label: "Perdidas" },
  { key: "total", label: "Total" },
  { key: "age", label: "Idade média (dias)" },
] as const;

export type OpportunityListColumnOptions = {
  hideCustomerColumn?: boolean;
  hideSellerColumn?: boolean;
  showOpenProposal?: boolean;
};

/** Filtra o catálogo conforme o contexto (página global vs Conta). */
export function resolveOpportunityListColumnCatalog(
  options: OpportunityListColumnOptions = {},
): OpportunityTableColumnItem[] {
  return OPPORTUNITY_LIST_COLUMN_CATALOG.filter((column) => {
    if (column.key === "customer" && options.hideCustomerColumn) return false;
    if (column.key === "seller" && options.hideSellerColumn) return false;
    if (column.key === "proposal-doc" && !options.showOpenProposal) return false;
    return true;
  });
}

export const OPPORTUNITY_LIST_EMPTY_FALLBACK_KEYS = ["ov", "status", "date"] as const;
export const OPPORTUNITY_COLLABORATOR_EMPTY_FALLBACK_KEYS = ["seller", "total"] as const;
