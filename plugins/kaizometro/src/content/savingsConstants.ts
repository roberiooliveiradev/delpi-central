/**
 * Projeção anual de economia = diária × dias úteis.
 * Espelha `ANNUAL_BUSINESS_DAYS` em
 * `api-delpi/.../kaizen_savings_calculator.py` — manter alinhado.
 *
 * Conta segunda a sexta, sem feriados (52×5 + 1).
 * Não confundir com a validade do kaizen (1 ano corrido desde a implantação).
 */
export const ANNUAL_BUSINESS_DAYS = 261;

export const ANNUAL_SAVINGS_FORMULA_LABEL = `economia/dia × ${ANNUAL_BUSINESS_DAYS} dias úteis`;

export const ANNUAL_SAVINGS_EXPLANATION =
  `A economia/ano é a diária multiplicada por ${ANNUAL_BUSINESS_DAYS} dias úteis ` +
  `(segunda a sexta, sem feriados) — base de operação industrial típica. ` +
  `Isso não é a validade do kaizen: a contabilização no painel segue 1 ano corrido ` +
  `desde a data de implantação.`;
