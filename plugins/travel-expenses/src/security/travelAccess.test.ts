import { describe, expect, it } from "vitest";

import { buildAccessFromPermissions, writableUnits } from "./travelAccess";

describe("buildAccessFromPermissions", () => {
  it("gives write + unit 01 to a traveler", () => {
    const access = buildAccessFromPermissions([
      "travel-expenses.view",
      "travel-expenses.write",
      "travel-expenses.unit.filial-01",
    ]);
    expect(access.canView).toBe(true);
    expect(access.canWrite).toBe(true);
    expect(access.canManage).toBe(false);
    expect(writableUnits(access).map((unit) => unit.id)).toEqual(["01"]);
  });

  it("admin sees both units without filial codes", () => {
    const access = buildAccessFromPermissions([], true);
    expect(access.admin).toBe(true);
    expect(access.units.map((unit) => unit.id)).toEqual(["01", "02"]);
  });
});
