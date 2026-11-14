import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  normalizeRequiredPermissions,
  userHasAnyPermission,
} from "./routePermission.ts";

describe("normalizeRequiredPermissions", () => {
  it("prioriza anyOfPermissions", () => {
    assert.deepEqual(
      normalizeRequiredPermissions("commercial.marketing", [
        "commercial.marketing",
        "commercial.manage",
      ]),
      ["commercial.marketing", "commercial.manage"],
    );
  });

  it("aceita permission como array", () => {
    assert.deepEqual(
      normalizeRequiredPermissions(["commercial.manage", "commercial.marketing"]),
      ["commercial.manage", "commercial.marketing"],
    );
  });
});

describe("userHasAnyPermission", () => {
  it("manage-only passa no any-of marketing|manage", () => {
    assert.equal(
      userHasAnyPermission(
        ["commercial.access", "commercial.manage"],
        ["commercial.marketing", "commercial.manage"],
      ),
      true,
    );
  });

  it("access-only falha no any-of", () => {
    assert.equal(
      userHasAnyPermission(
        ["commercial.access"],
        ["commercial.marketing", "commercial.manage"],
      ),
      false,
    );
  });
});
