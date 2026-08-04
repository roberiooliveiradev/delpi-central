import { createContext } from "react";

import type { SellerPortfolio } from "../types/sellerPortfolio";

export type PortfolioScopeContextValue = {
  loading: boolean;
  isAdmin: boolean;
  myPortfolio: SellerPortfolio | null;
  sellers: SellerPortfolio[];
  sellerIdFilter: string | null;
  setSellerIdFilter: (sellerId: string | null) => void;
  reloadScope: () => void;
};

export const PortfolioScopeContext = createContext<PortfolioScopeContextValue | null>(
  null,
);
