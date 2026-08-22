import { fetchOverview } from "../api/financialApi";
import { copy } from "../content/copy";
import type { FinancialBranch, OverviewPayload } from "../types";
import { useAsyncResource } from "./useAsyncResource";

export function useOverview(branch: FinancialBranch) {
  return useAsyncResource<OverviewPayload>(
    (signal) => fetchOverview({ branch, signal }),
    [branch],
    copy.home.loadError,
  );
}
