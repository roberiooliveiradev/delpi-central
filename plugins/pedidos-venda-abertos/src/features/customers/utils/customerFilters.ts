import type {
  CustomerAttentionFilter,
  CustomerSummary,
} from "../types/customerSummary.ts";
import { normalizeCadastroPart } from "./customerIdentity.ts";

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

export function matchesCustomerFilter(
  customer: CustomerSummary,
  filter: CustomerAttentionFilter,
): boolean {
  if (filter === "all") return true;
  if (filter === "overdue") return customer.temAtraso;
  if (filter === "partial") return customer.temPedidoParcial;
  return true;
}

export function filterCustomers(
  customers: readonly CustomerSummary[],
  search: string,
  filter: CustomerAttentionFilter,
): CustomerSummary[] {
  return customers.filter(
    (customer) =>
      matchesCustomerFilter(customer, filter) && matchesCustomerSearch(customer, search),
  );
}
