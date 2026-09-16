import { describe, expect, it } from "vitest";

import {
  buildSuppliesUnitOptions,
  formatSuppliesUnitName,
  formatSuppliesUnitLabel,
  normalizeSuppliesUnitCode,
  resolveDefaultBranch,
  resolveRequestedBranches,
} from "./suppliesUnits";

describe("suppliesUnits", () => {
  it("formats canonical units without TOTVS codes", () => {
    expect(formatSuppliesUnitName("01")).toBe("Santa Catarina");
    expect(formatSuppliesUnitName("02")).toBe("Espírito Santo");
    expect(formatSuppliesUnitLabel("01")).toBe("Santa Catarina");
    expect(formatSuppliesUnitLabel("02")).toBe("Espírito Santo");
  });

  it("falls back safely for unknown codes", () => {
    expect(formatSuppliesUnitName("99")).toBe("Filial 99");
    expect(formatSuppliesUnitName("")).toBe("—");
    expect(formatSuppliesUnitName(null)).toBe("—");
  });

  it("normalizes technical identity separately from presentation", () => {
    expect(normalizeSuppliesUnitCode("01")).toBe("01");
    expect(normalizeSuppliesUnitCode("Santa Catarina")).toBe("01");
    expect(normalizeSuppliesUnitCode("espírito santo")).toBe("02");
  });

  it("builds options only from allowedUnits and without codes in labels", () => {
    expect(buildSuppliesUnitOptions(["01"])).toEqual([
      { value: "01", label: "Santa Catarina" },
    ]);
    expect(buildSuppliesUnitOptions(["02"])).toEqual([
      { value: "02", label: "Espírito Santo" },
    ]);
    expect(buildSuppliesUnitOptions(["01", "02"]).map((o) => o.value)).toEqual([
      "01",
      "02",
    ]);
    expect(JSON.stringify(buildSuppliesUnitOptions(["01", "02"]))).not.toContain("(01)");
    expect(JSON.stringify(buildSuppliesUnitOptions(["01", "02"]))).not.toContain("(02)");
  });

  it("resolves default branch without inventing unauthorized units", () => {
    expect(resolveDefaultBranch(["01", "02"], "02")).toBe("02");
    expect(resolveDefaultBranch(["01"], "02")).toBe("01");
    expect(resolveDefaultBranch(["02"], "01")).toBe("02");
    expect(resolveDefaultBranch([], "01")).toBe("");
  });

  it("expands empty selection to all authorized units", () => {
    expect(resolveRequestedBranches([], ["01", "02"])).toEqual(["01", "02"]);
    expect(resolveRequestedBranches(["02"], ["01", "02"])).toEqual(["02"]);
    expect(resolveRequestedBranches(["02"], ["01"])).toEqual(["01"]);
    expect(resolveRequestedBranches(["99"], ["01", "02"])).toEqual(["01", "02"]);
  });
});
