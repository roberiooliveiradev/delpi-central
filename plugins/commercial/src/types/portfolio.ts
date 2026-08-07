export type SellerCustomer = {
  customer_code: string;
  customer_store: string;
  customer_name: string | null;
};

export type SellerCustomerInput = {
  customer_code: string;
  customer_store: string;
  customer_name?: string | null;
};

export type SellerPortfolio = {
  id: string;
  user_id: string;
  display_name: string;
  active: boolean;
  customer_count: number;
  customers: SellerCustomer[];
};

export type CommercialCapabilities = {
  worklist_view: boolean;
  followups_manage: boolean;
  seller_portfolios_manage: boolean;
  analytics_view: boolean;
  proposals_view: boolean;
  proposals_export: boolean;
  accounts_team_view: boolean;
  worklist_team_view: boolean;
  team_scope: boolean;
};

export type SellerPortfolioMeResponse = {
  /** Sempre o usuário autenticado (mesmo sem carteira). */
  user_id?: string | null;
  portfolio: SellerPortfolio | null;
  is_admin: boolean;
  capabilities?: CommercialCapabilities;
};

export type CustomerEnrichmentItem = {
  customer_code: string;
  customer_store: string;
  city: string | null;
  state: string | null;
  last_purchase_date: string | null;
  billed_12m: number;
  billed_recent_6m?: number;
  billed_prior_6m?: number;
  billing_trend?: "up" | "down" | "stable" | "insufficient";
  billing_trend_pct?: number | null;
  has_avatar: boolean;
  avatar_url: string | null;
};

export type TotvsCustomerHit = {
  code: string;
  store: string;
  name: string;
  blocked?: string | null;
};

export type TransferSellerCustomersResult = {
  source: SellerPortfolio;
  target: SellerPortfolio;
  transferred_count: number;
};

export type DirectoryUser = {
  id: string;
  name: string;
  email: string;
};
