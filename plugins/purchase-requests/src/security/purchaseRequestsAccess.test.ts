import { describe, expect, it } from "vitest";

import { buildAccessFromPermissions } from "./purchaseRequestsAccess";

describe("purchaseRequestsAccess", () => {
  it("grants canAdmin to rbac.manage holders", () => {
    const access = buildAccessFromPermissions(["rbac.manage"], false);
    expect(access.canAdmin).toBe(true);
  });

  it("requires purchase-requests.admin for canAdmin", () => {
    const withAccessOnly = buildAccessFromPermissions(
      ["purchase-requests.access", "purchase-requests.unit.filial-01"],
      false,
    );
    expect(withAccessOnly.canView).toBe(true);
    expect(withAccessOnly.canAdmin).toBe(false);

    const withAdmin = buildAccessFromPermissions(
      ["purchase-requests.access", "purchase-requests.admin"],
      false,
    );
    expect(withAdmin.canAdmin).toBe(true);
  });

  it("exposes branches from unit permissions", () => {
    const access = buildAccessFromPermissions(
      [
        "purchase-requests.access",
        "purchase-requests.unit.filial-02",
      ],
      false,
    );
    expect(access.canView).toBe(true);
    expect(access.branches.map((branch) => branch.value)).toEqual(["02"]);
  });
});
