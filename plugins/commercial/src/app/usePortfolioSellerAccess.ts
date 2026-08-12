import { useMemo } from "react";

import { usePortfolioScope } from "./PortfolioScopeContext";

export type PortfolioSellerAccess = {
  allowSellerId: boolean;
  validSellerIds: readonly string[];
};

/**
 * Fonte única do `seller_id` aceito na URL (pedidos e carteira).
 * Vale para equipe (team.view) e para quem participa de mais de uma carteira própria.
 */
export function usePortfolioSellerAccess(): PortfolioSellerAccess {
  const { canFilterPortfolios, filterablePortfolios } = usePortfolioScope();
  return useMemo(
    () => ({
      allowSellerId: canFilterPortfolios,
      validSellerIds: canFilterPortfolios
        ? filterablePortfolios.map((portfolio) => portfolio.id)
        : [],
    }),
    [canFilterPortfolios, filterablePortfolios],
  );
}

export function portfolioSellerAccessKey(access: PortfolioSellerAccess): string {
  return `${access.allowSellerId ? "team" : "own"}:${access.validSellerIds.join(",")}`;
}
