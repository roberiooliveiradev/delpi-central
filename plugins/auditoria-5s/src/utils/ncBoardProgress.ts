import type { NcBoardItem } from "../types/ncManagement";

type NcBoardProgressSource = Pick<
  NcBoardItem,
  | "status"
  | "description"
  | "root_cause"
  | "corrective_action"
  | "responsible_name"
  | "due_date"
  | "has_before_evidence"
  | "has_after_evidence"
>;

/**
 * Checklist alinhado a `is_nc_plan_complete` (API) + foto do antes
 * exigida para finalizar a ação (depois é opcional).
 */
const NC_BOARD_PROGRESS_CHECKS: Array<(item: NcBoardProgressSource) => boolean> = [
  (item) => (item.description ?? "").trim().length >= 3,
  (item) => (item.root_cause ?? "").trim().length >= 3,
  (item) => (item.corrective_action ?? "").trim().length >= 3,
  (item) => (item.responsible_name ?? "").trim().length >= 2,
  (item) => Boolean(item.due_date),
  (item) => Boolean(item.has_before_evidence),
];

export const NC_BOARD_PROGRESS_STEP_COUNT = NC_BOARD_PROGRESS_CHECKS.length;

/** Percentual 0–100 conforme campos obrigatórios / evidências preenchidos. */
export function computeNcBoardProgressPct(item: NcBoardProgressSource): number {
  if (item.status === "closed") return 100;
  const done = NC_BOARD_PROGRESS_CHECKS.reduce(
    (count, check) => count + (check(item) ? 1 : 0),
    0,
  );
  return Math.round((done / NC_BOARD_PROGRESS_STEP_COUNT) * 100);
}
