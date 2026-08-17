import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { pickPrimaryRolTarget, resolveGapToTarget } from "./gapToTarget.ts";

describe("gapToTarget", () => {
  it("returns null without target", () => {
    assert.equal(resolveGapToTarget({ rol: 10, target: null, rol_target_pct: null }), null);
  });

  it("returns max(target - rol, 0)", () => {
    assert.equal(resolveGapToTarget({ rol: 40, target: 100, rol_target_pct: 40 }), 60);
    assert.equal(resolveGapToTarget({ rol: 120, target: 100, rol_target_pct: 120 }), 0);
  });

  it("picks branch ROL when unit filter is set", () => {
    const head = { rol: 1, target: 2, rol_target_pct: 50 };
    const branch = { rol: 3, target: 4, rol_target_pct: 75 };
    assert.equal(pickPrimaryRolTarget(head, branch, "02"), branch);
    assert.equal(pickPrimaryRolTarget(head, branch, null), head);
  });
});
