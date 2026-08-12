/**
 * Resolve códigos TOTVS de clientes a partir das carteiras do escopo.
 * sellerId null → consolidado (sem filtro de codes).
 */
import type { SellerPortfolio } from "../../../types/portfolio";

export function resolvePortfolioCustomerCodes(
  sellerId: string | null,
  portfolios: readonly SellerPortfolio[],
): string[] | null {
  if (!sellerId) return null;
  const portfolio = portfolios.find((item) => item.id === sellerId);
  if (!portfolio) return [];
  const seen = new Set<string>();
  const codes: string[] = [];
  for (const customer of portfolio.customers ?? []) {
    const code = (customer.customer_code || "").trim();
    if (!code || seen.has(code)) continue;
    seen.add(code);
    codes.push(code);
  }
  return codes;
}

export function serializeCustomerCodesCsv(codes: string[] | null | undefined): string | undefined {
  if (codes == null) return undefined;
  return codes.join(",");
}
