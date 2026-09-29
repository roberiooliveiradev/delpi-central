import type { ProductionRunSnapshot, RunDowntimeView } from "./api";
import type { MachineLoadRealtimeEvent } from "./usePublicMachineLoadRealtime";

export function applyProductionRunPiecesSnapshot(
  run: ProductionRunSnapshot | null,
  event: MachineLoadRealtimeEvent | null,
  branch: string,
  workCenter: string | null,
): ProductionRunSnapshot | null {
  if (
    !run ||
    event?.type !== "production_run_updated" ||
    event.reason !== "pieces_updated" ||
    event.branch !== branch ||
    event.workCenter !== workCenter ||
    event.runId !== run.id ||
    typeof event.piecesTotal !== "number" ||
    !Number.isFinite(event.piecesTotal)
  ) {
    return run;
  }
  return {
    ...run,
    piecesTotal: event.piecesTotal,
    countedPieces: event.piecesTotal,
    divergencePieces: undefined,
  };
}

const RUN_DOWNTIME_REASONS = new Set([
  "downtime_classified",
  "automatic_downtime_started",
  "automatic_downtime_ended",
]);

/**
 * Mescla downtime/operationalState de eventos `downtime_classified` e
 * `automatic_downtime_*` no snapshot do run (merge instantâneo; a
 * reconciliação HTTP via runUpdatedSignal segue autoritativa).
 */
export function applyProductionRunDowntimeEvent(
  run: ProductionRunSnapshot | null,
  event: MachineLoadRealtimeEvent | null,
  branch: string,
  workCenter: string | null,
): ProductionRunSnapshot | null {
  const downtime = event?.downtime as RunDowntimeView | undefined;
  if (
    !run ||
    event?.type !== "production_run_updated" ||
    !RUN_DOWNTIME_REASONS.has(event.reason) ||
    event.branch !== branch ||
    event.workCenter !== workCenter ||
    event.runId !== run.id ||
    (event.reason === "downtime_classified" && !downtime)
  ) {
    return run;
  }
  const next: ProductionRunSnapshot = { ...run };
  if (downtime) next.downtime = downtime;
  if (event.reason === "automatic_downtime_ended") {
    next.downtime = null;
    next.pendingDowntime = downtime ?? next.pendingDowntime;
    next.pendingDowntimeCount = downtime ? 1 : next.pendingDowntimeCount;
  }
  if (typeof event.operationalState === "string") {
    next.operationalState = event.operationalState;
  }
  if (typeof event.piecesTotal === "number" && Number.isFinite(event.piecesTotal)) {
    next.piecesTotal = event.piecesTotal;
    next.countedPieces = event.piecesTotal;
    next.divergencePieces = undefined;
  }
  return next;
}
