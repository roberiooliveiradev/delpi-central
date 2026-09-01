import { fetchBillingDashboard } from "../api/financialApi";
import { copy } from "../content/copy";
import type { BillingDashboard, FinancialBranch } from "../types";
import { useAsyncResource } from "./useAsyncResource";

export function useBilling(
  branch: FinancialBranch,
  startDate: string | null,
  endDate: string | null,
  granularity: string | null,
) {
  return useAsyncResource<BillingDashboard>(
    (signal) =>
      fetchBillingDashboard({
        branch,
        startDate,
        endDate,
        granularity,
        signal,
      }),
    [branch, startDate, endDate, granularity],
    copy.billing.loadError,
  );
}
