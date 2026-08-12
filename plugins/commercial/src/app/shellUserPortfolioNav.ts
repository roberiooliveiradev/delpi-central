import {
  buildCustomersListSearch,
  type CustomersListSellerAccess,
} from "../utils/customersListDeepLink";

export type ShellUserPortfolioOption = {
  id: string;
  displayName: string;
};

export type ShellUserPortfolioNavMode =
  | { kind: "disabled" }
  | { kind: "direct"; portfolio: ShellUserPortfolioOption }
  | { kind: "menu"; portfolios: ShellUserPortfolioOption[] };

/** Normaliza carteiras com id para o menu da TopBar. */
export function toShellUserPortfolioOptions(
  portfolios: ReadonlyArray<{ id: string; display_name: string }>,
): ShellUserPortfolioOption[] {
  return portfolios
    .map((portfolio) => ({
      id: portfolio.id.trim(),
      displayName: (portfolio.display_name || "").trim() || portfolio.id.trim(),
    }))
    .filter((portfolio) => Boolean(portfolio.id));
}

/**
 * 0 carteiras → não clicável; 1 → ir direto; N → listar para escolher.
 */
export function resolveShellUserPortfolioNavMode(
  portfolios: ReadonlyArray<{ id: string; display_name: string }>,
): ShellUserPortfolioNavMode {
  const options = toShellUserPortfolioOptions(portfolios);
  if (options.length === 0) return { kind: "disabled" };
  if (options.length === 1) return { kind: "direct", portfolio: options[0]! };
  return { kind: "menu", portfolios: options };
}

export function shellPortfolioSellerAccess(
  portfolioIds: readonly string[],
): CustomersListSellerAccess {
  const ids = portfolioIds.map((id) => id.trim()).filter(Boolean);
  return {
    allowSellerId: ids.length > 1,
    validSellerIds: ids.length > 1 ? ids : [],
  };
}

/** Query de Minha Carteira já filtrada pela carteira (quando o usuário tem mais de uma). */
export function buildShellPortfolioCustomersSearch(
  portfolioId: string,
  portfolioIds: readonly string[],
): string {
  return buildCustomersListSearch(
    { sellerId: portfolioId },
    shellPortfolioSellerAccess(portfolioIds),
  );
}
