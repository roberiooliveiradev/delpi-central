import type { SellerPortfolio } from "../types/portfolio";

/** Compat com imports PVA (`reloadScope` ↔ `reload`). */
export type PortfolioScopeContextValue = {
  loading: boolean;
  error?: string | null;
  isAdmin: boolean;
  myPortfolio: SellerPortfolio | null;
  sellers: SellerPortfolio[];
  sellerIdFilter: string | null;
  setSellerIdFilter: (sellerId: string | null) => void;
  reload: () => void;
  /** Alias PVA */
  reloadScope: () => void;
};
