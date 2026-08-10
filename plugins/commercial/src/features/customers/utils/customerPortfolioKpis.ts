import type { CustomerSummary } from "../types/customerSummary";

const DAY_MS = 24 * 60 * 60 * 1000;

/**
 * Dias corridos desde a última venda (nota fiscal).
 * `null` se não houver data válida.
 */
export function daysSinceLastSale(
  lastSaleDate: string | null | undefined,
  today: Date = new Date(),
): number | null {
  const raw = (lastSaleDate || "").trim();
  if (!raw) return null;
  const parsed = new Date(`${raw.slice(0, 10)}T12:00:00`);
  if (Number.isNaN(parsed.getTime())) return null;
  const startOfToday = new Date(today);
  startOfToday.setHours(12, 0, 0, 0);
  const diff = Math.floor((startOfToday.getTime() - parsed.getTime()) / DAY_MS);
  return Math.max(0, diff);
}

/**
 * Cliente sem venda há pelo menos `days` dias.
 * Ausência de enrichment é desconhecida e não entra no KPI/filtro.
 */
export function isWithoutSaleForDays(
  customer: Pick<CustomerSummary, "lastPurchaseDate">,
  days: number,
  today: Date = new Date(),
): boolean {
  const elapsed = daysSinceLastSale(customer.lastPurchaseDate, today);
  if (elapsed === null) return false;
  return elapsed >= days;
}

export function countCustomersWithoutSaleForDays(
  customers: readonly Pick<CustomerSummary, "lastPurchaseDate">[],
  days: number,
  today: Date = new Date(),
): number {
  return customers.filter((customer) => isWithoutSaleForDays(customer, days, today)).length;
}

/** Clientes ativos: com pedidos em aberto e status diferente de inativo. */
export function countActivePortfolioCustomers(
  customers: readonly Pick<CustomerSummary, "status" | "quantidadePedidosAbertos">[],
): number {
  return customers.filter((customer) => {
    if (customer.quantidadePedidosAbertos <= 0) return false;
    if (customer.status === "inativo") return false;
    return true;
  }).length;
}
