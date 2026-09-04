import type { TableSortDirection } from "../../../utils/sortTableRows";

/** UI column key → api-delpi `sort_by` (CommercialProposalsRepository._list_order_clause). */
export const PROPOSAL_COLUMN_TO_SORT_BY: Record<string, string> = {
  ov: "proposal_number",
  rev: "revision",
  customer: "customer_code",
  status: "status_code",
  stage: "stage",
  date: "proposal_date",
};

export const DEFAULT_PROPOSAL_SORT_KEY = "date";
export const DEFAULT_PROPOSAL_SORT_DIR: TableSortDirection = "desc";

export function proposalApiSortParams(
  sortKey: string,
  sortDirection: TableSortDirection,
): { sort_by: string; sort_dir: TableSortDirection } {
  return {
    sort_by: PROPOSAL_COLUMN_TO_SORT_BY[sortKey] ?? "proposal_date",
    sort_dir: sortDirection,
  };
}
