export type ReportDefinition = {
  id: string;
  name: string;
  providerKey: string;
  params: Record<string, unknown>;
  active: boolean;
  createdByUserId: string | null;
  createdAt: string | null;
  updatedAt: string | null;
};

export type ReportDefinitionsList = {
  items: ReportDefinition[];
  total: number;
};

export type ReportRecipient = {
  id: string;
  definitionId: string;
  userId: string;
  email: string;
  active: boolean;
};

export type ReportSchedule = {
  id: string;
  definitionId: string;
  scheduleKind: "daily" | "weekly" | "weekdays" | "monthly" | string;
  cronExpression: string | null;
  timezone: string;
  nextRunAt: string | null;
  enabled: boolean;
  hour: number | null;
  minute: number | null;
  weekday: number | null;
  dayOfMonth?: number | null;
};

export type ReportProviderInfo = {
  key: string;
  paramsSchema: Record<string, unknown>;
};

export type ReportDelivery = {
  id: string;
  runId: string;
  recipientEmail: string;
  status: string;
  error: string | null;
  sentAt: string | null;
};

export type ReportRun = {
  id: string;
  definitionId: string;
  trigger: string;
  status: string;
  startedAt: string | null;
  finishedAt: string | null;
  summary: Record<string, unknown>;
  error: string | null;
  createdAt: string | null;
  deliveries?: ReportDelivery[];
};

export type DirectoryUser = {
  id: string;
  name: string;
  email: string;
};

export type ShortageItemNote = {
  id: string;
  definitionId: string;
  branch: string;
  productCode: string;
  noteText: string;
  expectedReceiptDate: string | null;
  authorUserId: string;
  authorDisplayName: string;
  createdAt: string | null;
  updatedAt: string | null;
};

export type ShortageItemNotesList = {
  items: ShortageItemNote[];
  total: number;
  definitionId: string;
  branch: string;
};

export type ShortagePreviewItem = {
  product_code: string;
  product_description?: string;
  observation?: string;
};

export type SafetyBelowOrder = {
  order_number: string;
  order_item: string;
  supplier_name: string;
  warehouse: string;
  open_quantity: number;
  order_unit: string;
  open_quantity_primary_unit: number | null;
  expected_delivery_date: string | null;
  delivery_status: "scheduled" | "overdue" | "without_date";
  coverage_eligible: boolean;
};

export type SafetyBelowItem = {
  branch: string;
  product_code: string;
  product_description: string;
  unit: string;
  available_stock: number;
  safety_stock: number;
  deficit_quantity: number;
  eligible_open_quantity: number;
  projected_stock_after_orders: number;
  remaining_to_buy: number;
  coverage_status: "sufficient" | "partial" | "none";
  next_expected_delivery_date: string | null;
  purchase_orders: SafetyBelowOrder[];
  open_order_count: number;
  warnings: string[];
  is_stockout: boolean;
};

export type SafetyBelowPreviewData = {
  items: SafetyBelowItem[];
  total: number;
  title: string;
  meta: {
    branch: string;
    asOfDate: string;
    alertCount: number;
    coveredCount: number;
    partialCount: number;
    uncoveredCount: number;
    stockoutCount: number;
  };
  providerKey: string;
};
