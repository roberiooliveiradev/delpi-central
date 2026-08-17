import type {
  CustomerListFocus,
  CustomerListTrend,
} from "../../../utils/customersListDeepLink.ts";
import type { CustomerSummary } from "../types/customerSummary.ts";
import { normalizeCadastroPart } from "./customerIdentity.ts";
import { isWithoutSaleForDays } from "./customerPortfolioKpis.ts";

function includesInsensitive(haystack: string, needle: string): boolean {
  if (!needle) return true;
  return haystack.toLocaleLowerCase("pt-BR").includes(needle);
}

/**
 * Busca local (sem API): código, loja, nome, pedido, pedido_cliente.
 * Não remove zeros à esquerda do termo (apenas trim).
 */
export function matchesCustomerSearch(
  customer: CustomerSummary,
  rawQuery: string,
): boolean {
  const query = rawQuery.trim().toLocaleLowerCase("pt-BR");
  if (!query) return true;

  if (includesInsensitive(customer.codigo, query)) return true;
  if (includesInsensitive(customer.loja, query)) return true;
  if (includesInsensitive(customer.nome, query)) return true;
  if (includesInsensitive(customer.sellerName ?? "", query)) return true;
  if (includesInsensitive(`${customer.codigo}-${customer.loja}`, query)) return true;

  for (const line of customer.lines) {
    if (includesInsensitive(normalizeCadastroPart(line.pedido), query)) return true;
    if (includesInsensitive(normalizeCadastroPart(line.pedido_cliente), query)) return true;
    if (includesInsensitive(normalizeCadastroPart(line.filial), query)) return true;
  }

  return false;
}

export function matchesOperationalFocus(
  customer: CustomerSummary,
  focus: CustomerListFocus,
): boolean {
  if (focus === "all") return true;
  if (focus === "attention") return customer.status === "atencao";
  if (focus === "active") return customer.status === "ativo";
  if (focus === "no_sale_60") return isWithoutSaleForDays(customer, 60);
  return true;
}

export function matchesBillingTrend(
  customer: CustomerSummary,
  trend: CustomerListTrend,
): boolean {
  if (trend === "all") return true;
  return customer.billingTrend === trend;
}

/** Compatível com o recorte operacional; tendência entra em `filterCustomers`. */
export function matchesCustomerFilter(
  customer: CustomerSummary,
  filter: CustomerListFocus,
): boolean {
  return matchesOperationalFocus(customer, filter);
}

export function filterCustomers(
  customers: readonly CustomerSummary[],
  search: string,
  focus: CustomerListFocus,
  trend: CustomerListTrend = "all",
): CustomerSummary[] {
  return customers.filter(
    (customer) =>
      matchesOperationalFocus(customer, focus) &&
      matchesBillingTrend(customer, trend) &&
      matchesCustomerSearch(customer, search),
  );
}
