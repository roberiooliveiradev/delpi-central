import type { ActionPlanSummary } from "../types/actionPlan";

export type PlansFilterState = {
  statuses: string[];
  severities: string[];
  branches: string[];
  scopes: string[];
  customerName: string;
  productCode: string;
  ownerUserId: string;
  department: string;
  rootCauseCategory: string;
  overdueOnly: boolean;
};

export const EMPTY_PLANS_FILTERS: PlansFilterState = {
  statuses: [],
  severities: [],
  branches: [],
  scopes: [],
  customerName: "",
  productCode: "",
  ownerUserId: "",
  department: "",
  rootCauseCategory: "",
  overdueOnly: false,
};

export function applyClientPlanFilters(
  items: ActionPlanSummary[],
  filters: PlansFilterState,
): ActionPlanSummary[] {
  const customer = filters.customerName.trim().toLocaleLowerCase("pt-BR");
  const product = filters.productCode.trim().toLocaleLowerCase("pt-BR");

  return items.filter((plan) => {
    if (filters.statuses.length && !filters.statuses.includes(plan.status)) return false;
    if (filters.severities.length && !filters.severities.includes(plan.severity)) return false;
    if (filters.branches.length && !filters.branches.includes(plan.branch_code ?? "")) return false;
    if (filters.scopes.length && !filters.scopes.includes(plan.nonconformity_scope ?? "")) return false;
    if (customer && !(plan.customer_name ?? "").toLocaleLowerCase("pt-BR").includes(customer)) {
      return false;
    }
    if (product && !(plan.product_code ?? "").toLocaleLowerCase("pt-BR").includes(product)) {
      return false;
    }
    return true;
  });
}

export function buildListApiParams(filters: PlansFilterState) {
  return {
    status: filters.statuses.length === 1 ? filters.statuses[0] : undefined,
    severity: filters.severities.length === 1 ? filters.severities[0] : undefined,
    branch_code: filters.branches.length === 1 ? filters.branches[0] : undefined,
    nonconformity_scope: filters.scopes.length === 1 ? filters.scopes[0] : undefined,
    customer_name: filters.customerName.trim() || undefined,
    product_code: filters.productCode.trim() || undefined,
    owner_user_id: filters.ownerUserId.trim() || undefined,
    department: filters.department.trim() || undefined,
    root_cause_category: filters.rootCauseCategory.trim() || undefined,
    overdue_only: filters.overdueOnly || undefined,
    page_size: 200,
  };
}

export function needsClientSideFilter(filters: PlansFilterState): boolean {
  return filters.statuses.length > 1 || filters.severities.length > 1 || filters.branches.length > 1
    || filters.scopes.length > 1;
}
