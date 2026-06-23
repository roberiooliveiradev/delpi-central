import type { CommercialFilterUrlState } from "../utils/filterUrl";
import { appendFiltersToPath } from "../utils/filterUrl";
import { resolveCommercialApiBranch } from "../utils/commercialClientFilters";

export const COMMERCIAL_BASE_PATH = "/apps/dashboard-commercial";

export const COMMERCIAL_ROUTES = {
  home: COMMERCIAL_BASE_PATH,
} as const;

export type CommercialDetailUrlState = CommercialFilterUrlState & {
  revision?: string;
  proposalBranch?: string;
};

export function buildCommercialDetailPath(
  proposalNumber: string,
  state: CommercialDetailUrlState
): string {
  const encoded = encodeURIComponent(String(proposalNumber).trim());
  const branch = (
    state.proposalBranch ||
    resolveCommercialApiBranch(state.branches) ||
    ""
  ).trim();
  const params = new URLSearchParams();

  if (state.dateStart) params.set("start_date", state.dateStart);
  if (state.dateEnd) params.set("end_date", state.dateEnd);
  if (branch) params.set("branch", branch);
  if (state.customerSegment) {
    params.set("customer_segment", state.customerSegment);
  }
  if (state.revision) params.set("revision", state.revision);

  const query = params.toString();
  return `${COMMERCIAL_BASE_PATH}/ov/${encoded}${query ? `?${query}` : ""}`;
}

export { appendFiltersToPath };
