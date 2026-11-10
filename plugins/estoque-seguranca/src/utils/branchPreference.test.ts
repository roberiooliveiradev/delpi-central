// @vitest-environment jsdom

import { afterEach, describe, expect, it } from "vitest";
import type { SafetyStockFiltersData } from "../types/safetyStock";
import {
  readPreferredSafetyStockBranch,
  resolveAuthorizedSafetyStockBranch,
  savePreferredSafetyStockBranch,
} from "./branchPreference";

function options(authorized: string[], branch = authorized[0] ?? ""): SafetyStockFiltersData {
  return { authorized_branches: authorized, branch } as SafetyStockFiltersData;
}

afterEach(() => window.localStorage.clear());

describe("preferência de filial de estoque (#1195)", () => {
  it("preserva a filial 02 no reload e nas duas abas", () => {
    savePreferredSafetyStockBranch("02");
    expect(readPreferredSafetyStockBranch()).toBe("02");
    expect(resolveAuthorizedSafetyStockBranch("", options(["01", "02"]), readPreferredSafetyStockBranch())).toBe("02");
  });

  it("prioriza a mudança explícita feita pelo usuário", () => {
    expect(resolveAuthorizedSafetyStockBranch("01", options(["01", "02"]), "02")).toBe("01");
  });

  it("ignora filial gravada sem autorização e usa uma filial permitida", () => {
    expect(resolveAuthorizedSafetyStockBranch("", options(["01"]), "02")).toBe("01");
    expect(resolveAuthorizedSafetyStockBranch("02", options(["01"]), "02")).toBe("01");
    expect(resolveAuthorizedSafetyStockBranch("", null, "02")).toBe("");
    expect(resolveAuthorizedSafetyStockBranch("", options([]), "02")).toBe("");
  });

  it("descarta preferências inválidas e nunca salva uma filial desconhecida", () => {
    savePreferredSafetyStockBranch("99");
    expect(readPreferredSafetyStockBranch()).toBe("");
    window.localStorage.setItem("estoque-seguranca:preferred-branch:v1", "99");
    expect(readPreferredSafetyStockBranch()).toBe("");
  });
});
