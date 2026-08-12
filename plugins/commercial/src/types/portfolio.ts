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

export type SellerPortfolioMemberRole = "owner" | "member";

export type SellerPortfolioMember = {
  user_id: string;
  role: SellerPortfolioMemberRole;
};

export type SellerPortfolio = {
  id: string;
  /** Dono legado (espelho do owner) — preferir `owner_user_id`/`members`. */
  user_id: string;
  owner_user_id?: string | null;
  display_name: string;
  active: boolean;
  customer_count: number;
  /** Quantidade de membros (owner + members); fallback 1 se members vazio. */
  member_count?: number;
  customers: SellerCustomer[];
  members?: SellerPortfolioMember[];
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
  /** Primeira carteira — compat com consumidores single-portfolio. */
  portfolio: SellerPortfolio | null;
  /** Todas as carteiras em que o usuário é owner ou member. */
  portfolios?: SellerPortfolio[];
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

export type PortfolioCoverageRef = {
  id: string;
  display_name: string;
};

export type OverlappingCustomerCoverage = {
  customer_code: string;
  customer_store: string;
  customer_name: string | null;
  portfolio_ids: string[];
  portfolios: PortfolioCoverageRef[];
};

export type PortfolioOverlapSummary = {
  id: string;
  display_name: string;
  overlapping_customer_count: number;
};

export type PortfolioCoverageGapStatus = {
  available: boolean;
  reason: string | null;
};

export type SellerPortfoliosCoverageAudit = {
  overlapping_count: number;
  overlapping: OverlappingCustomerCoverage[];
  portfolios_with_overlap: PortfolioOverlapSummary[];
  gap: PortfolioCoverageGapStatus;
};

export type TotvsLoadMetricsStatus = {
  available: boolean;
  reason: string | null;
};

export type PortfolioLoadItem = {
  id: string;
  display_name: string;
  active: boolean;
  customer_count: number;
  member_count: number;
  open_value: number | null;
  attention_count: number | null;
};

export type PersonLoadItem = {
  user_id: string;
  portfolio_ids: string[];
  portfolio_count: number;
  customer_count: number;
  open_value: number | null;
  attention_count: number | null;
};

export type SellerPortfoliosLoadSummary = {
  portfolios: PortfolioLoadItem[];
  by_person: PersonLoadItem[];
  totvs_metrics: TotvsLoadMetricsStatus;
};

export type CoverageLinkWarning = {
  code: string;
  message: string;
  other_portfolios: PortfolioCoverageRef[];
};

export type AddSellerCustomerResult = SellerPortfolio & {
  warnings?: CoverageLinkWarning[];
  coverage_warning?: CoverageLinkWarning | null;
};

export type SellerPortfolioAuditTone =
  | "default"
  | "danger"
  | "warning"
  | "success"
  | "info";

export type SellerPortfolioAuditEvent = {
  id: string;
  action: string;
  actor_user_id: string;
  entity_type: string;
  entity_id: string;
  payload: Record<string, unknown>;
  created_at: string | null;
  title: string;
  message: string;
  tone: SellerPortfolioAuditTone;
};

export type SellerPortfolioAuditPage = {
  items: SellerPortfolioAuditEvent[];
  total: number;
  page: number;
  page_size: number;
};

export type DirectoryUser = {
  id: string;
  name: string;
  email: string;
};
