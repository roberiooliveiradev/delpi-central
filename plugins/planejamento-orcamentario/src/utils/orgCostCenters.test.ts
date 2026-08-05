import { describe, expect, it } from "vitest";

import {
  costCenterKey,
  formatCostCenterLabel,
  isSameCostCenter,
  matchesCostCenterSearch,
  normalizeBranchCode,
} from "./orgCostCenters";

describe("orgCostCenters", () => {
  it("normaliza apenas filiais 01 e 02", () => {
    expect(normalizeBranchCode("01")).toBe("01");
    expect(normalizeBranchCode("02")).toBe("02");
    expect(normalizeBranchCode("99")).toBe("");
  });

  it("formata sempre com filial + código + descrição", () => {
    expect(
      formatCostCenterLabel({ branch: "01", code: "1234", description: "Produção" }),
    ).toBe("Filial 01 · 1234 — Produção");
  });

  it("usa chave composta ou id interno sem colidir códigos iguais", () => {
    expect(costCenterKey({ branch: "01", code: "1234" })).toBe("01:1234");
    expect(costCenterKey({ branch: "02", code: "1234" })).toBe("02:1234");
    expect(costCenterKey({ id: "uuid-1", branch: "01", code: "1234" })).toBe("id:uuid-1");
    expect(costCenterKey({ branch: "01", code: "1234" })).not.toBe(
      costCenterKey({ branch: "02", code: "1234" }),
    );
  });

  it("compara centros pelo par filial+código", () => {
    expect(
      isSameCostCenter(
        { branch: "01", code: "205" },
        { unit_code: "01", code: "205" },
      ),
    ).toBe(true);
    expect(
      isSameCostCenter({ branch: "01", code: "205" }, { branch: "02", code: "205" }),
    ).toBe(false);
  });

  it("filtra busca por código e descrição", () => {
    const cc = { branch: "01", code: "1234", description: "Produção" };
    expect(matchesCostCenterSearch(cc, "123")).toBe(true);
    expect(matchesCostCenterSearch(cc, "produ")).toBe(true);
    expect(matchesCostCenterSearch(cc, "manut")).toBe(false);
  });
});
