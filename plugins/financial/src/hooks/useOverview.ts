import { fetchOverview } from "../api/financialApi";
import { copy } from "../content/copy";
import type { FinancialBranch, OverviewPayload } from "../types";
import { useAsyncResource } from "./useAsyncResource";

export function useOverview(
  branch: FinancialBranch,
  startDate: string | null = null,
  endDate: string | null = null,
) {
  return useAsyncResource<OverviewPayload>(
    (signal) => fetchOverview({ branch, startDate, endDate, signal }),
    [branch, startDate, endDate],
    copy.home.loadError,
  );
}
