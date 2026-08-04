import type { SellerPortfolio } from "../../../types/sellerPortfolio";
import { buildCustomerKey } from "./customerIdentity.ts";

/**
 * Mapa código|loja → nome do(s) vendedor(es) da carteira.
 * Se o cliente estiver em mais de uma carteira, junta os nomes com " · ".
 */
export function buildSellerNameByCustomerKey(
  sellers: readonly Pick<SellerPortfolio, "display_name" | "customers">[],
): Map<string, string> {
  const namesByKey = new Map<string, string[]>();
  for (const seller of sellers) {
    const displayName = seller.display_name.trim();
    if (!displayName) continue;
    for (const customer of seller.customers) {
      const key = buildCustomerKey(customer.customer_code, customer.customer_store);
      if (!key) continue;
      const names = namesByKey.get(key) ?? [];
      if (!names.includes(displayName)) {
        names.push(displayName);
      }
      namesByKey.set(key, names);
    }
  }
  const result = new Map<string, string>();
  for (const [key, names] of namesByKey) {
    result.set(key, names.join(" · "));
  }
  return result;
}
