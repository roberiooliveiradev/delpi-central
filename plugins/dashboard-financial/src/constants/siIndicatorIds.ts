/** indicator_id canônicos do Strategic Indicators (departamento financial). */
export const FINANCIAL_SI_INDICATORS = {
  /** ROL financeiro usa a mesma source_key SI do comercial (`commercial_rol`). */
  rol: "commercial-rol",
  ebitda: "financial-ebitda",
  fixedCost: "financial-fixed-cost",
  pmr: "financial-pmr",
} as const;
