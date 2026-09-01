/** `all` = consolidado das duas filiais; o BFF exige as duas permissões. */
export type FinancialBranch = "01" | "02" | "all";
export type SubpluginStatus = "active" | "coming_soon";

export type Subplugin = {
  id: string;
  label: string;
  description: string;
  icon: string;
  route: string;
  status: SubpluginStatus;
  permission: string;
};

export type SubpluginsPayload = {
  items: Subplugin[];
  capabilities: { export: boolean };
};

export type Period = {
  startDate: string | null;
  endDate: string | null;
  endDateExclusive: string | null;
  label: string | null;
};

export type Pagination = {
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
  isComplete: boolean;
};

export type SortState = {
  sortBy: string;
  sortDir: "asc" | "desc";
};

// ---------------------------------------------------------------- inadimplência

export type DelinquencyTotals = {
  titles: number;
  onTimeTitles: number;
  lateTitles: number;
  totalAmount: number;
  onTimeAmount: number;
  lateAmount: number;
};

export type DelinquencyIndicators = {
  onTimePctByCount: number;
  onTimePctByAmount: number;
  latePctByCount: number;
  latePctByAmount: number;
  averageDaysLate: number;
};

export type DelinquencySummary = {
  period: Period;
  scopeNotice: string;
  totals: DelinquencyTotals;
  indicators: DelinquencyIndicators;
};

export type DelinquencyMonthPoint = {
  month: string;
  yearMonth: string;
  totalTitles: number;
  onTimeTitles: number;
  lateTitles: number;
  totalAmount: number;
  onTimeAmount: number;
  lateAmount: number;
  onTimePctByCount: number;
  onTimePctByAmount: number;
};

export type DelinquencyAgingBucket = {
  code: string;
  label: string;
  order: number;
  count: number;
  amount: number;
  countPct: number;
  amountPct: number;
};

export type DelinquencyCustomer = {
  customerCode: string;
  store: string;
  customerName: string;
  shortName: string;
  totalTitles: number;
  onTimeTitles: number;
  lateTitles: number;
  totalAmount: number;
  lateAmount: number;
  onTimePctByCount: number;
  onTimePctByAmount: number;
};

export type DelinquencyTitle = {
  branch: string;
  prefix: string;
  number: string;
  installment: string;
  type: string;
  customerCode: string;
  store: string;
  customerName: string;
  shortName: string;
  issueDate: string | null;
  dueDate: string | null;
  paymentDate: string | null;
  amount: number;
  paidOnTime: boolean;
  daysLate: number;
  delayRange: { code: string; label: string };
};

export type DelinquencyCustomersPayload = {
  period: Period;
  pagination: Pagination;
  sort: SortState;
  items: DelinquencyCustomer[];
};

export type DelinquencyTitlesPayload = {
  period: Period;
  pagination: Pagination;
  sort: SortState;
  filters: {
    customerCode: string | null;
    store: string | null;
    status: string;
    delayRange: string | null;
    search: string | null;
  };
  items: DelinquencyTitle[];
};

// ------------------------------------------------------------- centro de custo

export type FilterOption = { code: string; label: string; store?: string };

export type CostCenterFiltersPayload = {
  period: Period;
  branch: string | null;
  branches: FilterOption[];
  costCenters: FilterOption[];
  suppliers: FilterOption[];
};

export type CostCenterSummary = {
  period: Period;
  branch: string | null;
  totalAmount: number;
  entryCount: number;
  costCenterCount: number;
  supplierCount: number;
  averageTicket: number;
  largestEntry: number;
};

export type CostCenterSeriesPoint = {
  yearMonth: string;
  year: number;
  month: number;
  totalAmount: number;
  entryCount: number;
};

export type CostCenterRankingItem = {
  code: string;
  label: string;
  store?: string;
  totalAmount: number;
  entryCount: number;
  percentage: number;
};

export type CostCenterEntry = {
  id: string;
  branch: string;
  issueDate: string | null;
  issueDateLabel: string;
  costCenterCode: string;
  costCenterLabel: string;
  supplierCode: string;
  supplierStore: string;
  supplierName: string;
  document: string;
  series: string;
  purchaseOrder: string;
  item: string;
  orderItem: string;
  productCode: string;
  productLabel: string;
  notes: string;
  quantity: number;
  unitAmount: number;
  totalAmount: number;
  ledgerAccount: string;
  apportionment: string;
  tes: string;
  cfop: string;
  documentType: string;
  entryType: string;
};

export type CostCenterEntriesPayload = {
  period: Period;
  branch: string | null;
  pagination: Pagination;
  sort: SortState;
  filters: {
    costCenter: string | null;
    supplierCode: string | null;
    supplierStore: string | null;
    search: string | null;
  };
  items: CostCenterEntry[];
};

// ------------------------------------------------------------------ indicadores

export type StrategicIndicator = {
  indicatorId: string;
  name: string;
  weightPct: number;
  goalLabel: string | null;
  goalValue: number;
  goalPeriodicity: string | null;
  goalMode: string | null;
  performanceDirection: string | null;
  value: number;
  hasValue: boolean;
  score: number;
  gap: number;
  classification: string | null;
  valueUnit: string | null;
  valuePrefix: string | null;
  valueSuffix: string | null;
  valueDecimals: number;
};

export type DepartmentIndicators = {
  available: boolean;
  reason?: string;
  detail?: string | null;
  departmentId?: string;
  departmentName?: string;
  shortName?: string;
  idd?: number;
  classification?: string | null;
  contribution?: number;
  aggregationMode?: string | null;
  partialSuccess?: boolean;
  notice?: string | null;
  indicators?: StrategicIndicator[];
};

export type GlobalIndicators = {
  available: boolean;
  reason?: string;
  detail?: string | null;
  igd?: number;
  classification?: string | null;
  trendDirection?: string | null;
  bestDepartment?: string | null;
  primaryRisk?: string | null;
  competence?: string | null;
};

// -------------------------------------------------------------- gestão à vista

export type BlockState = {
  available: boolean;
  error: string | null;
  detail?: string | null;
};

export type KpiBlock = BlockState & {
  label?: string;
  unit?: string;
  value?: number;
  target?: number;
  amount?: number;
  grossRevenue?: number;
  taxes?: number;
};

export type BillingLine = {
  key: string;
  label: string;
  value: number;
  role?: string | null;
};

export type BillingSummary = {
  period: Period;
  branch: string | null;
  rol: number;
  target: number | null;
  targetPct: number | null;
  gap: number | null;
  goalLabel: string | null;
  grossRevenue: number;
  otherValues: number;
  itemsWithoutTes: number;
  returns: number;
  discounts: number;
  icms: number;
  iss: number;
  pis: number;
  cofins: number;
  ipiSeparated: number;
  taxes: number;
  financialTitles: number;
  financialBalance: number;
  composition: BillingLine[];
  taxMix: BillingLine[];
  detail: BillingLine[];
};

export type BillingSeriesPoint = {
  period: string;
  sortKey: string;
  startDate: string;
  endDate: string;
  rol01: number;
  rol02: number;
};

export type BillingSeriesBlock = BlockState & {
  granularity?: string;
  truncated?: boolean;
  items?: BillingSeriesPoint[];
};

export type BillingCustomer = {
  customerCode: string;
  customerStore: string;
  customerName: string;
  rol: number;
  grossRevenue: number;
  sharePct: number | null;
  rank: number;
};

export type BillingCustomersBlock = BlockState & {
  branch?: string | null;
  items?: BillingCustomer[];
  others?: BillingCustomer | null;
  totalRol?: number;
  customersCount?: number;
};

export type BillingBranchItem = {
  branch: string;
  rol: number;
  grossRevenue: number;
  returns: number;
  discounts: number;
};

export type BillingBranchesBlock = BlockState & {
  items?: BillingBranchItem[];
  totalRol?: number;
};

export type BillingDashboard = {
  branch: string | null;
  period: { startDate: string; endDate: string };
  granularity: string;
  summary: BillingSummary;
  series: BillingSeriesBlock;
  customers: BillingCustomersBlock;
  branches: BillingBranchesBlock;
};

export type BillingInvoice = {
  kind: string;
  kindLabel: string;
  branch: string;
  issueDate: string;
  invoiceNumber: string;
  series: string;
  customerCode: string;
  customerStore: string;
  customerName: string;
  gross: number;
  discounts: number;
  returns: number;
  taxes: number;
  rol: number;
};

export type BillingInvoicesPayload = {
  branch: string | null;
  period: { startDate: string; endDate: string };
  truncated: boolean;
  items: BillingInvoice[];
  totals: {
    count: number;
    gross: number;
    discounts: number;
    returns: number;
    taxes: number;
    rol: number;
  };
};

export type OverviewDelinquencyBlock = BlockState & {
  period?: Period;
  scopeNotice?: string;
  totals?: DelinquencyTotals;
  indicators?: DelinquencyIndicators;
  series?: DelinquencyMonthPoint[];
};

export type OverviewCostCentersBlock = BlockState & {
  period?: Period;
  totalAmount?: number;
  entryCount?: number;
  costCenterCount?: number;
  averageTicket?: number;
  top?: CostCenterRankingItem[];
};

export type OverviewIndicatorsBlock = BlockState & {
  department?: DepartmentIndicators;
};

export type OverviewPayload = {
  branch: string | null;
  period: { startDate: string; endDate: string };
  blocks: {
    rol: KpiBlock;
    ebitda: KpiBlock;
    fixedCost: KpiBlock;
    pmr: KpiBlock;
    delinquency: OverviewDelinquencyBlock;
    costCenters: OverviewCostCentersBlock;
    indicators: OverviewIndicatorsBlock;
  };
};
