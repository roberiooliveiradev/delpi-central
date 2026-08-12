import { describe, expect, it } from "vitest";

import { canExport, resolveAuthorizedBranches } from "./permissions";

describe("permissions", () => {
  it("libera ambas filiais com access global", () => {
    expect(resolveAuthorizedBranches({ permissions: ["materiais-terceiros.access"] })).toEqual([
      "01",
      "02",
    ]);
  });

  it("filtra só SC quando o JWT tem filial-sc", () => {
    expect(
      resolveAuthorizedBranches({ permissions: ["materiais-terceiros.view.filial-sc"] }),
    ).toEqual(["01"]);
  });

  it("usa hasPermission do portal quando informado", () => {
    expect(
      resolveAuthorizedBranches({
        hasPermission: (code) => code === "materiais-terceiros.view.filial-es",
      }),
    ).toEqual(["02"]);
  });

  it("exporta com permissão dedicada", () => {
    expect(canExport({ permissions: ["materiais-terceiros.export"] })).toBe(true);
    expect(canExport({ permissions: ["materiais-terceiros.view.filial-sc"] })).toBe(false);
  });
});
