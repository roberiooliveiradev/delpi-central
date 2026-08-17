import type { SellerPortfolio } from "../../../types/portfolio";
import { buildCustomerKey } from "./customerIdentity";

/**
 * True se o par código/loja aparece em alguma carteira do viewer (membership).
 */
export function isCustomerInViewerPortfolios(
  codigo: string,
  loja: string,
  portfolios: readonly SellerPortfolio[],
): boolean {
  const key = buildCustomerKey(codigo, loja);
  if (!key) return false;
  for (const portfolio of portfolios) {
    for (const customer of portfolio.customers ?? []) {
      if (
        buildCustomerKey(customer.customer_code, customer.customer_store) === key
      ) {
        return true;
      }
    }
  }
  return false;
}

/**
 * Topbar «Cliente» efêmero: só quando o detalhe está fora das carteiras do user
 * e o viewer não tem team/manage (esses tratam Conta como «dentro»).
 */
export function shouldShowEphemeralClientNav(options: {
  inMembership: boolean;
  canUseTeamScope: boolean;
  canManagePortfolios: boolean;
  isAdmin?: boolean;
}): boolean {
  if (
    options.canUseTeamScope ||
    options.canManagePortfolios ||
    options.isAdmin
  ) {
    return false;
  }
  return !options.inMembership;
}
