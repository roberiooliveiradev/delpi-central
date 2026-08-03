import { describe, expect, it } from "vitest";

import { resolveBranchFieldOptions } from "./BranchField";

describe("resolveBranchFieldOptions", () => {
  it("usa enum do schema quando não há branchScope", () => {
    expect(resolveBranchFieldOptions(null, ["01", "02"])).toEqual(["01", "02"]);
  });

  it("inclui Todas quando enum traz Todas e consolidado é permitido", () => {
    expect(resolveBranchFieldOptions(null, ["Todas", "01", "02"])).toEqual([
      "Todas",
      "01",
      "02",
    ]);
    expect(
      resolveBranchFieldOptions(
        { branches: ["01", "02"], allowConsolidated: true },
        ["Todas", "01", "02"],
      ),
    ).toEqual(["Todas", "01", "02"]);
  });

  it("omite Todas quando consolidado não é permitido", () => {
    expect(
      resolveBranchFieldOptions(
        { branches: ["01"], allowConsolidated: false },
        ["Todas", "01", "02"],
      ),
    ).toEqual(["01"]);
  });

  it("usa filiais do scope quando não há enum", () => {
    expect(
      resolveBranchFieldOptions({ branches: ["01"], allowConsolidated: true }, null),
    ).toEqual(["01"]);
  });

  it("intersecta scope com enum da API", () => {
    expect(
      resolveBranchFieldOptions(
        { branches: ["01", "02", "99"], allowConsolidated: true },
        ["01", "02"],
      ),
    ).toEqual(["01", "02"]);
  });

  it("se a interseção for vazia, mantém o scope (RBAC)", () => {
    expect(
      resolveBranchFieldOptions({ branches: ["03"], allowConsolidated: false }, ["01", "02"]),
    ).toEqual(["03"]);
  });
});