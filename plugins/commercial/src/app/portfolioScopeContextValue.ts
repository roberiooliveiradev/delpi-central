import type { SellerPortfolio } from "../types/portfolio";

/** Compat com imports CM (`reloadScope` ↔ `reload`). */
export type PortfolioScopeContextValue = {
  loading: boolean;
  error?: string | null;
  isAdmin: boolean;
  canViewWorklist?: boolean;
  canManageFollowups?: boolean;
  canViewAnalytics?: boolean;
  canViewProposals?: boolean;
  canExportProposals?: boolean;
  canUseTeamScope?: boolean;
  canViewWorklistTeam?: boolean;
  myPortfolio: SellerPortfolio | null;
  myPortfolios?: SellerPortfolio[];
  canFilterPortfolios?: boolean;
  filterablePortfolios?: SellerPortfolio[];
  sellers: SellerPortfolio[];
  sellerIdFilter: string | null;
  setSellerIdFilter: (sellerId: string | null) => void;
  reload: () => void;
  /** Alias CM */
  reloadScope: () => void;
};
