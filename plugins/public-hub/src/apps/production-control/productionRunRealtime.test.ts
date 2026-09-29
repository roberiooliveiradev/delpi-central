import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type { ProductionRunSnapshot } from "./api.ts";
import {
  applyProductionRunDowntimeEvent,
  applyProductionRunPiecesSnapshot,
} from "./productionRunRealtime.ts";

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

describe("downtime_classified realtime event", () => {
  it("merges the classified downtime into the run snapshot", () => {
    const paused: ProductionRunSnapshot = {
      ...run,
      status: "paused",
      downtime: {
        id: "dt-1",
        runId: "run-1",
        reasonCode: null,
        reasonLabel: null,
        category: null,
        note: null,
        confirmed: false,
        startedAt: "2026-01-01T10:00:00Z",
        endedAt: null,
      },
    };
    const updated = applyProductionRunDowntimeEvent(
      paused,
      {
        type: "production_run_updated",
        reason: "downtime_classified",
        branch: "01",
        workCenter: "CT01",
        runId: "run-1",
        downtime: {
          id: "dt-1",
          runId: "run-1",
          reasonCode: "raw_material",
          reasonLabel: "Falta de material",
          category: "material",
          note: null,
          confirmed: true,
          startedAt: "2026-01-01T10:00:00Z",
          endedAt: null,
        },
      },
      "01",
      "CT01",
    );
    assert.equal(updated?.downtime?.reasonCode, "raw_material");
    assert.equal(updated?.downtime?.confirmed, true);
    assert.equal(updated?.id, "run-1");
  });

  it("does not replace the open downtime with an already-ended classified one", () => {
    // Regressão: classificar uma parada antiga não pode sobrescrever a
    // parada aberta (o timer passava a contar o startedAt da antiga).
    const stopped: ProductionRunSnapshot = {
      ...run,
      downtime: {
        id: "dt-current",
        runId: "run-1",
        reasonCode: null,
        reasonLabel: null,
        category: null,
        note: null,
        confirmed: false,
        startedAt: "2026-01-01T12:00:00Z",
        endedAt: null,
      },
      pendingDowntime: {
        id: "dt-old",
        runId: "run-1",
        reasonCode: null,
        reasonLabel: null,
        category: null,
        note: null,
        confirmed: false,
        startedAt: "2026-01-01T10:00:00Z",
        endedAt: "2026-01-01T10:30:00Z",
      },
      pendingDowntimeCount: 1,
    };
    const updated = applyProductionRunDowntimeEvent(
      stopped,
      {
        type: "production_run_updated",
        reason: "downtime_classified",
        branch: "01",
        workCenter: "CT01",
        runId: "run-1",
        downtime: {
          id: "dt-old",
          runId: "run-1",
          reasonCode: "raw_material",
          reasonLabel: "Falta de material",
          category: "material",
          note: null,
          confirmed: true,
          startedAt: "2026-01-01T10:00:00Z",
          endedAt: "2026-01-01T10:30:00Z",
        },
      },
      "01",
      "CT01",
    );
    assert.equal(updated?.downtime?.id, "dt-current");
    assert.equal(updated?.pendingDowntime, null);
    assert.equal(updated?.pendingDowntimeCount, 0);
  });

  it("ignores the event when the downtime payload is missing", () => {
    const updated = applyProductionRunDowntimeEvent(
      run,
      {
        type: "production_run_updated",
        reason: "downtime_classified",
        branch: "01",
        workCenter: "CT01",
        runId: "run-1",
      },
      "01",
      "CT01",
    );
    assert.equal(updated, run);
  });
});
