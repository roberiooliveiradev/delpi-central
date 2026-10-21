import { describe, expect, it } from "vitest";

import { allows, METALOGRAPHY_PERMISSIONS } from "./permissions";

describe("permissions", () => {
  it("hides edit from a view-only user and keeps it for superadmin", () => {
    expect(allows([METALOGRAPHY_PERMISSIONS.view], false, METALOGRAPHY_PERMISSIONS.edit)).toBe(false);
    expect(allows([METALOGRAPHY_PERMISSIONS.view], false, METALOGRAPHY_PERMISSIONS.view)).toBe(true);
    expect(allows([], true, METALOGRAPHY_PERMISSIONS.delete)).toBe(true);
  });

  it("does not invent a local allow when the host omitted the permission list", () => {
    expect(allows(undefined, false, METALOGRAPHY_PERMISSIONS.export)).toBe(true);
  });
});
