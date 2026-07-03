/**
 * Catálogo SI (departamento comercial, indicador único ROL per_unit).
 * Pesos usados apenas em textos de ajuda; pontuação é calculada no strategic-indicators-api.
 */
export const COMMERCIAL_KPI_TITLES = {
  /** Indicador único `commercial-rol` (scope per_unit) no SI. */
  rol: "ROL",
  rolWeg: "ROL WEG",
  rolNewBusiness: "ROL Novos Negócios",
  salesOrderOtd: "OTD — pedidos de venda",
  closingRate: "Taxa de conversão",
  newBusinessRol: "% ROL — novos negócios",
} as const;

export const COMMERCIAL_SI_INDICATOR_IDS = {
  rol: "commercial-rol",
  rolWeg: "commercial-rol-weg",
  rolNewBusiness: "commercial-rol-new-business",
  closingRate: "commercial-closing-rate",
  salesOrderOtd: "commercial-sales-order-otd",
  newBusinessRol: "commercial-new-business-rol-pct",
} as const;

export const COMMERCIAL_ROL_SERIES_LABELS = {
  filial01: "ROL Santa Catarina",
  filial02: "ROL Espírito Santo",
} as const;

/** Como o realizado consolidado é agregado na UI (metas continuam por unidade). */
export const COMMERCIAL_CONSOLIDATED_BRANCH_LABELS = {
  sum: "Consolidado (soma das unidades)",
  average: "Consolidado (média das unidades)",
  allBranches: "Consolidado (todas as unidades)",
} as const;
