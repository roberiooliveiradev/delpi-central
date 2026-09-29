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

/** Mescla o downtime do evento `downtime_classified` no snapshot do run. */
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
    event.reason !== "downtime_classified" ||
    event.branch !== branch ||
    event.workCenter !== workCenter ||
    event.runId !== run.id ||
    !downtime
  ) {
    return run;
  }
  return { ...run, downtime };
}
