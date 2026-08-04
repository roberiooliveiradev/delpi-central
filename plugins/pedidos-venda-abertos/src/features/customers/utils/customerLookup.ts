import type { CustomerSummary } from "../types/customerSummary.ts";
import { buildCustomerKey } from "./customerIdentity.ts";

/**
 * Localiza cliente exclusivamente por código + loja (mesma chave da agregação).
 * Não muta a lista. Não busca por nome.
 */
export function findCustomerByIdentity(
  customers: readonly CustomerSummary[],
  codigo: string | null | undefined,
  loja: string | null | undefined,
): CustomerSummary | null {
  const key = buildCustomerKey(codigo, loja);
  if (!key) return null;
  for (const customer of customers) {
    if (customer.key === key) return customer;
  }
  return null;
}
