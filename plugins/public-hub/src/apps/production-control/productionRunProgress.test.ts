import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  piecesToOperatorUnit,
  resolveProductionRunProgress,
} from "./productionRunProgress.ts";

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

describe("pieces to operator unit", () => {
  it("converts absolute pieces to milheiro reading (MI factor 1000)", () => {
    assert.equal(piecesToOperatorUnit(10, 1000), 0.01);
    assert.equal(piecesToOperatorUnit(1, 1000), 0.001);
    assert.equal(piecesToOperatorUnit(520, 1000), 0.52);
  });

  it("keeps pieces unchanged for piece units (factor 1)", () => {
    assert.equal(piecesToOperatorUnit(520, 1), 520);
  });

  it("does not invent a conversion when the factor is missing or invalid", () => {
    assert.equal(piecesToOperatorUnit(7, null), 7);
    assert.equal(piecesToOperatorUnit(7, undefined), 7);
    assert.equal(piecesToOperatorUnit(7, 0), 7);
    assert.equal(piecesToOperatorUnit(7, Number.NaN), 7);
  });
});
