import { copy } from "../content/copy";
import type { DemandLine, DemandStatus } from "../types";

export type DemandStatusBadge = {
  label: string;
  variant: "danger" | "warning" | "info" | "success";
};

const BADGES: Record<DemandStatus, DemandStatusBadge> = {
  late: { label: copy.demand.status.late, variant: "danger" },
  at_risk: { label: copy.demand.status.at_risk, variant: "warning" },
  covered_by_order: { label: copy.demand.status.covered_by_order, variant: "info" },
  covered_by_stock: { label: copy.demand.status.covered_by_stock, variant: "success" },
};

export function demandStatusBadge(status: string | null | undefined): DemandStatusBadge {
  return BADGES[status as DemandStatus] ?? BADGES.at_risk;
}

export function demandStatusOptions(statuses: readonly string[]): Array<{
  value: string;
  label: string;
}> {
  return statuses
    .filter((status): status is DemandStatus => status in BADGES)
    .map((status) => ({ value: status, label: BADGES[status].label }));
}

/** Linha que exige ação do PCP: venceu ou não tem quem produza o saldo. */
export function isDemandActionable(line: Pick<DemandLine, "status">): boolean {
  return line.status === "late" || line.status === "at_risk";
}
