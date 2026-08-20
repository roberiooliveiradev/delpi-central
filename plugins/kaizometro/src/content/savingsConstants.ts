/**
 * Projeção anual de economia = diária × dias úteis.
 * Espelha `ANNUAL_BUSINESS_DAYS` em
 * `api-delpi/.../kaizen_savings_calculator.py` — manter alinhado.
 *
 * Constante Delpi: 253 dias úteis/ano.
 * Não confundir com a validade do kaizen (1 ano corrido desde a implantação).
 */
export const ANNUAL_BUSINESS_DAYS = 253;

export const ANNUAL_SAVINGS_FORMULA_LABEL = `economia/dia × ${ANNUAL_BUSINESS_DAYS} dias úteis`;

export const ANNUAL_SAVINGS_EXPLANATION =
  `A economia/ano é a diária multiplicada por ${ANNUAL_BUSINESS_DAYS} dias úteis ` +
  `(constante Delpi para projeção). ` +
  `Isso não é a validade do kaizen: a contabilização no painel segue 1 ano corrido ` +
  `desde a data de implantação.`;
