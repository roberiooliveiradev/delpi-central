import type { LineFeederProductDetail, LineFeederStatus } from "../types";

const STATUS_RANK: Record<LineFeederStatus, number> = {
  at_risk: 0,
  unknown: 1,
  to_pick: 2,
  covered: 3,
};

export type LineFeederDetailTab = "overview" | "benches" | "movements";

export function worstLineFeederStatus(
  statuses: readonly string[],
): LineFeederStatus | null {
  let worst: LineFeederStatus | null = null;
  for (const raw of statuses) {
    if (!(raw in STATUS_RANK)) continue;
    const status = raw as LineFeederStatus;
    if (worst == null || STATUS_RANK[status] < STATUS_RANK[worst]) {
      worst = status;
    }
  }
  return worst;
}

/** Soma só quando todas as bancadas têm quantidade medida; senão não afirma total. */
export function sumKnownQuantities(
  values: ReadonlyArray<number | null | undefined>,
): number | null {
  if (values.length === 0) return 0;
  if (values.some((value) => value == null || Number.isNaN(value))) return null;
  return values.reduce<number>((total, value) => total + Number(value), 0);
}

export function pointOfUseQty(
  required: number | null,
  toDeliver: number | null,
): number | null {
  if (required == null || toDeliver == null) return null;
  return Math.max(required - toDeliver, 0);
}

export function summarizeLineFeederProductDetail(detail: LineFeederProductDetail): {
  status: LineFeederStatus | null;
  requiredQty: number | null;
  toDeliverQty: number | null;
  pointOfUseQty: number | null;
  destinations: string;
} {
  const requiredQty = sumKnownQuantities(
    detail.work_centers.map((row) => row.required_qty),
  );
  const toDeliverQty = sumKnownQuantities(
    detail.work_centers.map((row) => row.to_deliver_qty),
  );
  return {
    status: worstLineFeederStatus(detail.work_centers.map((row) => row.status)),
    requiredQty,
    toDeliverQty,
    pointOfUseQty: pointOfUseQty(requiredQty, toDeliverQty),
    destinations: detail.work_centers
      .map((row) => row.work_center_name || row.work_center)
      .filter(Boolean)
      .join(", "),
  };
}
