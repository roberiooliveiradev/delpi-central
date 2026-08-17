import { describe, expect, it } from "vitest";
import { resolveIssuancePermissions } from "./permissions";

describe("resolveIssuancePermissions", () => {
  it("libera tudo para superadmin", () => {
    const flags = resolveIssuancePermissions([], true);
    expect(flags.canCreate).toBe(true);
    expect(flags.canProcess).toBe(true);
    expect(flags.canManage).toBe(true);
  });

  it("create implica acesso de leitura", () => {
    const flags = resolveIssuancePermissions(["invoice-issuance.create"]);
    expect(flags.canCreate).toBe(true);
    expect(flags.canAccess).toBe(true);
    expect(flags.canProcess).toBe(false);
  });
});
