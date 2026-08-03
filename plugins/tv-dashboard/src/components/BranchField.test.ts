import { describe, expect, it } from "vitest";

import { resolveBranchFieldOptions } from "./BranchField";

describe("resolveBranchFieldOptions", () => {
  it("usa enum do schema quando não há branchScope", () => {
    expect(resolveBranchFieldOptions(null, ["01", "02"])).toEqual(["01", "02"]);
  });

  it("inclui all quando enum traz all e consolidado é permitido", () => {
    expect(resolveBranchFieldOptions(null, ["all", "01", "02"])).toEqual([
      "all",
      "01",
      "02",
    ]);
    expect(
      resolveBranchFieldOptions(
        { branches: ["01", "02"], allowConsolidated: true },
        ["all", "01", "02"],
      ),
    ).toEqual(["all", "01", "02"]);
  });

  it("omite all quando consolidado não é permitido", () => {
    expect(
      resolveBranchFieldOptions(
        { branches: ["01"], allowConsolidated: false },
        ["all", "01", "02"],
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