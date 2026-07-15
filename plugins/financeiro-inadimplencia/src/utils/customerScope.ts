/** Cliente intercompany Delpi — fora do escopo deste plugin. */
export const EXCLUDED_CUSTOMER_CODES = ["000207"] as const;

/** Cliente-chave WEG. Demais clientes = Novos Negócios. */
export const WEG_CUSTOMER_CODE = "000001";

export function isExcludedCustomer(codigo: string): boolean {
  return EXCLUDED_CUSTOMER_CODES.includes(
    codigo.trim() as (typeof EXCLUDED_CUSTOMER_CODES)[number],
  );
}

export function isWegCustomer(codigo: string): boolean {
  return codigo.trim() === WEG_CUSTOMER_CODE;
}

export function isNovosNegociosCustomer(codigo: string): boolean {
  const normalized = codigo.trim();
  return !isExcludedCustomer(normalized) && !isWegCustomer(normalized);
}
