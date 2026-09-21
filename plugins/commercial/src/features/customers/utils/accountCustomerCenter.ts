import type { SellerPortfolio } from "../../../types/portfolio";
import { buildCustomerKey, normalizeCadastroPart } from "./customerIdentity";

const STORAGE_PREFIX = "commercial:account-customer-center:";

function storageKey(codigo: string, loja: string): string | null {
  const key = buildCustomerKey(codigo, loja);
  return key ? `${STORAGE_PREFIX}${key}` : null;
}

/** Centro escolhido ao abrir a Conta — fora da URL. */
export function readAccountCustomerCenter(
  codigo: string,
  loja: string,
): string {
  if (typeof window === "undefined") return "";
  const key = storageKey(codigo, loja);
  if (!key) return "";
  try {
    return normalizeCadastroPart(window.sessionStorage.getItem(key));
  } catch {
    return "";
  }
}

export function writeAccountCustomerCenter(
  codigo: string,
  loja: string,
  customerCenter?: string | null,
): void {
  if (typeof window === "undefined") return;
  const key = storageKey(codigo, loja);
  if (!key) return;
  const center = normalizeCadastroPart(customerCenter);
  try {
    if (center) window.sessionStorage.setItem(key, center);
    else window.sessionStorage.removeItem(key);
  } catch {
    /* ignore quota / private mode */
  }
}

/**
 * Resolve o centro operacional da Conta sem colocar na URL:
 * 1) sessão (vindo da lista / Meus pedidos);
 * 2) único centro da membership para o par;
 * 3) vazio = loja inteira (fallback).
 */
export function resolveAccountCustomerCenter(options: {
  codigo: string;
  loja: string;
  portfolios?: readonly SellerPortfolio[];
}): string {
  const fromSession = readAccountCustomerCenter(options.codigo, options.loja);
  if (fromSession) return fromSession;

  const pair = buildCustomerKey(options.codigo, options.loja);
  if (!pair || !options.portfolios?.length) return "";

  const centers = new Set<string>();
  for (const portfolio of options.portfolios) {
    for (const customer of portfolio.customers ?? []) {
      if (
        buildCustomerKey(customer.customer_code, customer.customer_store) !== pair
      ) {
        continue;
      }
      centers.add(normalizeCadastroPart(customer.customer_center));
    }
  }
  if (centers.size === 1) {
    return [...centers][0] ?? "";
  }
  return "";
}
