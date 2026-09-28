import type { ProductionRunSnapshot } from "./api";
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
