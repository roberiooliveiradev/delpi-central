import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { resolveProductionRunProgress } from "./productionRunProgress.ts";

describe("production run progress", () => {
  it("evolves from 0 to 250 to 500 pieces", () => {
    assert.deepEqual(
      [0, 250, 500].map((counted) => resolveProductionRunProgress(counted, 500)?.progressPercent),
      [0, 50, 100],
    );
  });

  it("allows the absolute count and progress to decrease", () => {
    assert.equal(resolveProductionRunProgress(250, 500)?.visualPercent, 50);
    assert.equal(resolveProductionRunProgress(245, 500)?.visualPercent, 49);
  });

  it("keeps real overproduction while limiting only the visual width", () => {
    const progress = resolveProductionRunProgress(520, 500);
    assert.equal(progress?.progressPercent, 104);
    assert.equal(progress?.visualPercent, 100);
    assert.equal(progress?.overproductionPieces, 20);
    assert.equal(progress?.targetReached, true);
  });

  it("reaches the target only at or above target pieces", () => {
    assert.equal(resolveProductionRunProgress(499, 500)?.targetReached, false);
    assert.equal(resolveProductionRunProgress(500, 500)?.targetReached, true);
  });

  it("does not invent progress without a positive target", () => {
    assert.equal(resolveProductionRunProgress(10, null), null);
    assert.equal(resolveProductionRunProgress(10, 0), null);
  });
});
