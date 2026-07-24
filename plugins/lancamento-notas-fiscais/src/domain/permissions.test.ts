import { describe, expect, it } from "vitest";
import { resolveLnfPermissions } from "./permissions";
import { hasAction } from "./status";

describe("resolveLnfPermissions", () => {
  it("libera leitura para create/view/process/manage", () => {
    expect(resolveLnfPermissions(["lancamento-notas-fiscais.create"]).canRead).toBe(
      true,
    );
    expect(resolveLnfPermissions(["lancamento-notas-fiscais.view"]).canCreate).toBe(
      false,
    );
    expect(resolveLnfPermissions([], true).canManage).toBe(true);
  });
});

describe("hasAction", () => {
  it("respeita allowed_actions da API", () => {
    expect(hasAction(["start", "block"], "start")).toBe(true);
    expect(hasAction(["start"], "cancel")).toBe(false);
  });
});
