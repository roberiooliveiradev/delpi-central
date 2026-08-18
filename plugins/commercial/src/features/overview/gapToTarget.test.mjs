import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  pickPrimaryRolTarget,
  resolveGapToTarget,
  resolveOverviewGapToTarget,
} from "./gapToTarget.ts";

describe("gapToTarget", () => {
  it("returns null without comparable meta", () => {
    assert.equal(resolveGapToTarget({ rol: 10, target: null, rol_target_pct: null }), null);
    assert.equal(
      resolveGapToTarget({ rol: 10, target: 0, comparable_goal: 0, rol_target_pct: null }),
      null,
    );
  });

  it("uses comparable_goal over legacy target", () => {
    assert.equal(
      resolveGapToTarget({
        rol: 40,
        target: 999,
        comparable_goal: 100,
        rol_target_pct: 40,
      }),
      60,
    );
  });

  it("returns max(meta - rol, 0)", () => {
    assert.equal(resolveGapToTarget({ rol: 120, target: 100, rol_target_pct: 120 }), 0);
  });

  it("picks SC payload for branch 01 and ES for 02", () => {
    const head = { rol: 385755, target: 624774, comparable_goal: 624774, rol_target_pct: 62 };
    const es = { rol: 1852228, target: 2098452, comparable_goal: 2098452, rol_target_pct: 88 };
    assert.equal(pickPrimaryRolTarget(head, es, "01"), head);
    assert.equal(pickPrimaryRolTarget(head, es, "02"), es);
    assert.equal(pickPrimaryRolTarget(head, es, null), null);
  });

  it("overview gap with unit 01 is SC not ES", () => {
    const head = { rol: 385755.46, target: 624774.19, comparable_goal: 624774.19, rol_target_pct: 62 };
    const es = { rol: 1852227.52, target: 2098451.61, comparable_goal: 2098451.61, rol_target_pct: 88 };
    assert.equal(
      Math.round(resolveOverviewGapToTarget(head, es, "01") * 100) / 100,
      239018.73,
    );
    assert.equal(
      Math.round(resolveOverviewGapToTarget(head, es, "02") * 100) / 100,
      246224.09,
    );
  });

  it("overview without unit sums only slices that have meta", () => {
    const head = { rol: 100, target: 200, comparable_goal: 200, rol_target_pct: 50 };
    const es = { rol: 50, target: 0, comparable_goal: 0, rol_target_pct: null };
    assert.equal(resolveOverviewGapToTarget(head, es, null), 100);
    assert.equal(resolveOverviewGapToTarget(head, es, ""), 100);
  });
});
