import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type { ProductionRunSnapshot } from "./api.ts";
import { applyProductionRunPiecesSnapshot } from "./productionRunRealtime.ts";

const run: ProductionRunSnapshot = {
  id: "run-1",
  branch: "01",
  workCenter: "CT01",
  productionOrder: "OP1",
  operationCode: "10",
  deviceId: "device-1",
  operatorCode: "USR1",
  operatorName: null,
  status: "running",
  startedAt: null,
  endedAt: null,
  piecesTotal: 250,
  plannedQty: 0.5,
  targetPieces: 500,
  remainingPieces: 250,
  progressPercent: 50,
  targetReached: false,
  overproductionPieces: 0,
};

describe("production run realtime snapshot", () => {
  it("applies the absolute pieces value and preserves the frozen target", () => {
    const updated = applyProductionRunPiecesSnapshot(
      run,
      {
        type: "production_run_updated",
        reason: "pieces_updated",
        branch: "01",
        workCenter: "CT01",
        runId: "run-1",
        piecesTotal: 245,
      },
      "01",
      "CT01",
    );
    assert.equal(updated?.piecesTotal, 245);
    assert.equal(updated?.targetPieces, 500);
  });

  it("ignores snapshots for another run", () => {
    const updated = applyProductionRunPiecesSnapshot(
      run,
      {
        type: "production_run_updated",
        reason: "pieces_updated",
        branch: "01",
        workCenter: "CT01",
        runId: "run-2",
        piecesTotal: 500,
      },
      "01",
      "CT01",
    );
    assert.equal(updated, run);
  });
});
