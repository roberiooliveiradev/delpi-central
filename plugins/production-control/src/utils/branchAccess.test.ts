import { describe, expect, it } from "vitest";

import {
  ALL_PPC_BRANCHES,
  BRANCH_VIEW_PERMISSIONS,
  resolveActiveBranch,
  resolveAllowedBranches,
} from "./branchAccess";

describe("resolveAllowedBranches", () => {
  it("libera ambas as filiais para superadmin", () => {
    expect(resolveAllowedBranches([], true)).toEqual(["01", "02"]);
    expect(resolveAllowedBranches(undefined, true)).toEqual([...ALL_PPC_BRANCHES]);
  });

  it("filtra só as view.filial concedidas (caso P0: só 02)", () => {
    expect(
      resolveAllowedBranches(["production-control.access", BRANCH_VIEW_PERMISSIONS["02"]]),
    ).toEqual(["02"]);
  });

  it("caso irmão: só filial 01", () => {
    expect(resolveAllowedBranches([BRANCH_VIEW_PERMISSIONS["01"]])).toEqual(["01"]);
  });

  it("caso negativo: access sem filial não inventa 01", () => {
    expect(resolveAllowedBranches(["production-control.access"])).toEqual([]);
    expect(resolveAllowedBranches(undefined)).toEqual([]);
    expect(resolveAllowedBranches([])).toEqual([]);
  });

  it("ambas as filiais quando as duas permissões existem", () => {
    expect(
      resolveAllowedBranches([
        BRANCH_VIEW_PERMISSIONS["01"],
        BRANCH_VIEW_PERMISSIONS["02"],
      ]),
    ).toEqual(["01", "02"]);
  });
});

describe("resolveActiveBranch", () => {
  it("mantém a preferência quando autorizada", () => {
    expect(resolveActiveBranch(["01", "02"], "02")).toBe("02");
    expect(resolveActiveBranch(["01"], "01")).toBe("01");
  });

  it("troca preferência não autorizada pela primeira permitida (P0)", () => {
    expect(resolveActiveBranch(["02"], "01")).toBe("02");
    expect(resolveActiveBranch(["01"], "02")).toBe("01");
  });

  it("sem preferência usa a primeira permitida", () => {
    expect(resolveActiveBranch(["02"], null)).toBe("02");
    expect(resolveActiveBranch(["01", "02"], undefined)).toBe("01");
  });

  it("caso negativo: lista vazia não inventa filial", () => {
    expect(resolveActiveBranch([], "01")).toBeNull();
    expect(resolveActiveBranch([])).toBeNull();
  });
});
