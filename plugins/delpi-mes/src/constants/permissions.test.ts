import { describe, expect, it } from "vitest";

import { canUseDelpiMes, hasDelpiMesProductAccess } from "./permissions";

describe("Delpi MES permission flags", () => {
  it("requires declared permissions for regular users", () => {
    const permissions = new Set(["delpi-mes.access", "delpi-mes.monitoring.view"]);
    expect(hasDelpiMesProductAccess(permissions, false)).toBe(true);
    expect(canUseDelpiMes(permissions, "delpi-mes.monitoring.view", false)).toBe(true);
    expect(canUseDelpiMes(permissions, "delpi-mes.history.view", false)).toBe(false);
  });

  it("allows superadmin without inventing an admin permission", () => {
    expect(hasDelpiMesProductAccess(new Set(), true)).toBe(true);
    expect(canUseDelpiMes(new Set(), "delpi-mes.history.view", true)).toBe(true);
  });
});
