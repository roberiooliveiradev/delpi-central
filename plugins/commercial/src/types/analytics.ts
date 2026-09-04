import type { DashboardGoalFields } from "@delpi/plugin-ui/index";

export type AnalyticsCustomerSegment = "weg" | "new_business";

export type AnalyticsFilterParams = {
  start_date?: string;
  end_date?: string;
  branch?: string;
  customer_segment?: AnalyticsCustomerSegment;
  /** Filtro de carteira — commercial-api resolve customer_codes no servidor. CSV multi. */
  seller_id?: string;
  /** Filtro de clientes — commercial-api intersecta com membership. CSV de códigos TOTVS. */
  customer_codes?: string;
  /**
   * Conta 360: filtra OVs deste código sem membership de carteira
   * (`account_customer_code` no BFF).
   */
  account_customer_code?: string;
  status?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
  search?: string;
  /** Código de produto (ADJ) — listagem de OVs. */
  product_code?: string;
  /** Família/grupo Protheus (B1_GRUPO) — listagem de OVs. */
  product_group?: string;
  /** gross | net — faturamento da carteira (share/ranking). */
  nature?: "gross" | "net";
  /** CSV de códigos de produto (ROL by-product / by-customer). */
  product_codes?: string;
  /** CSV de famílias B1_GRUPO. */
  product_groups?: string;
  /** domestic | export */
  market?: "domestic" | "export";
};

export type RolTargetData = DashboardGoalFields & {
  branch?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  rol: number;
  target: number | null;
  rol_target_pct: number | null;
};

export type ClosingRateData = DashboardGoalFields & {
  branch?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  qtd_proposals: number;
  qtd_won: number;
  sales_conversion_rate_pct: number | null;
  /** Meta % do período (quando a API envia). */
  target?: number | null;
  comparable_goal?: number | null;
};

/** Snapshot KPI-CARTEIRA — BFF open-portfolio-summary (sem items). */
export type OpenPortfolioSummaryData = {
  openValue: number;
  openLineCount: number;
  asOf: string;
  nature: "open_order_value";
};

/** KPI-PORTFOLIO-SHARE — BFF portfolio-billing-share. */
export type PortfolioBillingShareData = {
  portfolioRol: number;
  companyRol: number;
  sharePct: number | null;
  startDate?: string | null;
  endDate?: string | null;
  branch?: string | null;
  /** gross | net — natureza do valor. */
  nature: "gross" | "net" | "portfolio_billing_share";
  /** Tag legada do KPI (quando o BFF ainda envia). */
  kpiNature?: "portfolio_billing_share";
  billingNature?: "gross" | "net";
};

/** Ranking delta % — BFF portfolio-billing-ranking. */
export type PortfolioBillingRankingItem = {
  customerCode?: string | null;
  customerStore?: string | null;
  customerName?: string | null;
  sellerName?: string | null;
  currentRol: number;
  priorRol: number;
  delta: number;
  deltaPct: number | null;
  rank: number;
};

export type PortfolioBillingRankingData = {
  groupBy: "customer" | "seller";
  order?: "growth" | "decline";
  items: PortfolioBillingRankingItem[];
  startDate: string;
  endDate: string;
  priorStartDate: string;
  priorEndDate: string;
  branch?: string | null;
  nature: "gross" | "net" | "portfolio_billing_ranking";
  kpiNature?: "portfolio_billing_ranking";
  billingNature?: "gross" | "net";
};

export type CommercialRolByProductItem = {
  product_code: string;
  product_group: string;
  product_name: string;
  domestic_rol: number;
  export_rol: number;
  rol: number;
  domestic_gross_revenue?: number;
  export_gross_revenue?: number;
  gross_revenue?: number;
  domestic_qty?: number;
  export_qty?: number;
  qty?: number;
  unit?: string | null;
  mixed_units?: boolean;
  share_pct?: number | null;
  rank?: number;
};

export type CommercialRolByProductData = {
  branch?: string;
  start_date?: string;
  end_date?: string;
  group_by?: "product" | "product_group";
  market?: string | null;
  items: CommercialRolByProductItem[];
  export_destination_countries?: string[];
  summary?: {
    total_rol?: number;
    total_gross_revenue?: number;
    total_qty?: number;
    items_count?: number;
  };
};

export type CommercialRolByCustomerItem = {
  customer_code: string;
  customer_store?: string;
  customer_name: string;
  cnpj?: string | null;
  city?: string | null;
  state?: string | null;
  rol: number;
  gross_revenue?: number;
  share_pct?: number | null;
  rank?: number;
};

export type CommercialRolByCustomerData = {
  branch?: string;
  start_date?: string;
  end_date?: string;
  items: CommercialRolByCustomerItem[];
  others?: CommercialRolByCustomerItem | null;
  summary?: {
    total_rol?: number;
    customers_count?: number;
    items_count?: number;
  };
};

export type OpenPortfolioHorizonBucketId =
  | "overdue"
  | "current_month"
  | "next_1_3_months"
  | "later"
  | "undated";

export type OpenPortfolioHorizonBucket = {
  id: OpenPortfolioHorizonBucketId;
  openValue: number;
  openLineCount: number;
};

/** KPI-CARTEIRA-HORIZON — BFF open-portfolio-horizon. */
export type OpenPortfolioHorizonData = {
  asOf: string;
  timezone: string;
  nature: "open_order_value_by_delivery";
  buckets: OpenPortfolioHorizonBucket[];
  totals: { openValue: number; openLineCount: number };
  scope?: { seller_id: string | null; mode: string };
};

export type SalesOrderOtdData = DashboardGoalFields & {
  branch?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  total_lines: number;
  on_time_lines: number;
  late_lines: number;
  sales_order_otd_pct: number | null;
};

export type NewBusinessRolPctData = DashboardGoalFields & {
  branch?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  total_rol: number;
  new_business_rol: number;
  weg_rol: number;
  new_business_rol_pct: number | null;
};

export type CommercialProposalStatusCategory = "won" | "lost" | "open" | "other";

export type CommercialProposal = {
  branch: string;
  proposal_number: string;
  revision: string;
  description?: string | null;
  proposal_date?: string | null;
  end_date?: string | null;
  status_code?: string | null;
  status_label?: string | null;
  status_category?: CommercialProposalStatusCategory | null;
  customer_code?: string | null;
  customer_store?: string | null;
  stage?: string | null;
  seller_code?: string | null;
  seller_name?: string | null;
};

export type CommercialProduct = {
  code: string;
  description?: string | null;
  group_code?: string | null;
  type?: string | null;
  qtd_pi?: number | null;
};

export type CommercialProposalHistoryEvent = {
  revision: string;
  process_code: string;
  stage_code: string;
  process_label?: string | null;
  stage_label?: string | null;
  start_date?: string | null;
  start_time?: string | null;
  end_date?: string | null;
  end_time?: string | null;
  duration_display?: string | null;
  duration_minutes?: number | null;
  status?: string | null;
  status_label?: string | null;
  is_open?: boolean;
  is_late?: boolean;
  is_current?: boolean;
  is_engineering?: boolean;
  is_engineering_flow?: boolean;
  is_engineering_entry?: boolean;
  flow_transition?: string | null;
  flow_transition_label?: string | null;
  flow_transition_labels?: string[] | null;
};

export type CommercialProposalDetail = CommercialProposal & {
  customer_name?: string | null;
  customer_store?: string | null;
  seller_code?: string | null;
  seller_name?: string | null;
  process_code?: string | null;
  process_label?: string | null;
  stage_label?: string | null;
  list_history?: CommercialProposalHistoryEvent[];
  list_products?: CommercialProduct[];
};

export type CommercialProposalHistoryEventsData = {
  items: CommercialProposalHistoryEvent[];
  total?: number;
  reference_revision?: string | null;
};

export type CommercialProposalsPage = {
  items: CommercialProposal[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type CommercialRolSeriesPoint = {
  periodo: string;
  sort_key: string;
  start_date: string;
  end_date: string;
  rol_matrix: number;
  rol_branch: number;
};

export type CommercialRolSeriesData = {
  granularity: string;
  truncated: boolean;
  points: CommercialRolSeriesPoint[];
};

export type SalesConversionRateSeriesPoint = {
  periodo: string;
  sort_key: string;
  start_date: string;
  end_date: string;
  conversion_filial_01: number | null;
  conversion_filial_02: number | null;
  qtd_proposals_01: number;
  qtd_proposals_02: number;
  qtd_won_01: number;
  qtd_won_02: number;
};

export type SalesConversionRateSeriesData = {
  granularity: string;
  truncated: boolean;
  points: SalesConversionRateSeriesPoint[];
};

export type SalesOrderOtdLineStatus = "on_time" | "late";

export type SalesOrderOtdLineItem = {
  branch: string;
  order_number: string;
  line_item: string;
  product_code?: string | null;
  product_description?: string | null;
  customer_code?: string | null;
  customer_store?: string | null;
  customer_name?: string | null;
  customer_short_name?: string | null;
  qty_sold?: number | null;
  qty_delivered?: number | null;
  promised_date?: string | null;
  invoice_date?: string | null;
  is_invoiced?: number | null;
  status: SalesOrderOtdLineStatus;
  days_diff?: number | null;
};

export type SalesOrderOtdRecurringCustomer = {
  customer_code: string;
  customer_store?: string | null;
  customer_name?: string | null;
  customer_short_name?: string | null;
  late_count: number;
  total_late_days?: number | null;
};

export type SalesOrderOtdPanelInsights = {
  recurringCustomers: SalesOrderOtdRecurringCustomer[];
  worstDelays: SalesOrderOtdLineItem[];
  upcomingPromises: SalesOrderOtdLineItem[];
};

export type SalesOrderOtdPanelData = {
  branch?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  summary: {
    total_lines: number;
    on_time_lines: number;
    late_lines: number;
    sales_order_otd_pct: number | null;
    late_percentage?: number | null;
    avg_late_days?: number | null;
    p50_late_days?: number | null;
    p90_late_days?: number | null;
  };
  insights?: SalesOrderOtdPanelInsights;
  lines: {
    items: SalesOrderOtdLineItem[];
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
};

export type SalesOrderOtdSeriesPoint = {
  periodo: string;
  sort_key: string;
  start_date: string;
  end_date: string;
  otd_filial_01: number | null;
  otd_filial_02: number | null;
  total_qty?: number | null;
  fulfilled_qty?: number | null;
  fulfillment_pct?: number | null;
  otd_pct?: number | null;
  total_lines?: number | null;
};

export type SalesOrderOtdSeriesData = {
  granularity: string;
  truncated: boolean;
  points: SalesOrderOtdSeriesPoint[];
};

export type SalesOrderOtdLineDetailData = {
  branch: string;
  order_number: string;
  line_item: string;
  line: SalesOrderOtdLineItem;
};

export type ChartGranularity = "day" | "week" | "month" | "year";
