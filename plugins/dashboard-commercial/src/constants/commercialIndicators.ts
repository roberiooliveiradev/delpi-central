/**
 * Catálogo SI (departamento comercial, indicador único ROL per_unit).
 * Pesos usados apenas em textos de ajuda; pontuação é calculada no strategic-indicators-api.
 */
export const COMMERCIAL_KPI_TITLES = {
  /** Indicador único `commercial-rol` (scope per_unit) no SI. */
  rol: "ROL",
  salesOrderOtd: "OTD — pedidos de venda",
  closingRate: "Taxa de conversão",
  newBusinessRol: "% ROL — novos negócios",
} as const;

export const COMMERCIAL_SI_INDICATOR_IDS = {
  rol: "commercial-rol",
  closingRate: "commercial-closing-rate",
  salesOrderOtd: "commercial-sales-order-otd",
  newBusinessRol: "commercial-new-business-rol",
} as const;

export const COMMERCIAL_ROL_SERIES_LABELS = {
  filial01: "ROL Filial 01",
  filial02: "ROL Filial 02",
} as const;

/** Como o realizado consolidado é agregado na UI (metas continuam por filial). */
export const COMMERCIAL_CONSOLIDATED_BRANCH_LABELS = {
  sum: "Consolidado (soma das filiais)",
  average: "Consolidado (média das filiais)",
  allBranches: "Consolidado (todas as filiais)",
} as const;
