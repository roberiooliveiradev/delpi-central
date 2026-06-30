export type DashboardFilterState = {
  branchCode: string;
  scope: string;
  customerName: string;
  productCode: string;
  failureMode: string;
};

export const EMPTY_DASHBOARD_FILTERS: DashboardFilterState = {
  branchCode: "",
  scope: "",
  customerName: "",
  productCode: "",
  failureMode: "",
};

export function buildDashboardApiParams(filters: DashboardFilterState) {
  return {
    branch_code: filters.branchCode || undefined,
    nonconformity_scope: filters.scope || undefined,
    customer_name: filters.customerName.trim() || undefined,
    product_code: filters.productCode.trim() || undefined,
    failure_mode: filters.failureMode.trim() || undefined,
  };
}
