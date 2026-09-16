import { describe, expect, it } from "vitest";

import {
  buildSuppliesUnitOptions,
  formatSuppliesUnitLabel,
  resolveDefaultBranch,
} from "./suppliesUnits";

describe("suppliesUnits", () => {
  it("formats canonical units with name and code", () => {
    expect(formatSuppliesUnitLabel("01")).toBe("Santa Catarina (01)");
    expect(formatSuppliesUnitLabel("02")).toBe("Espírito Santo (02)");
  });

  it("falls back safely for unknown codes", () => {
    expect(formatSuppliesUnitLabel("99")).toBe("Filial 99");
    expect(formatSuppliesUnitLabel("")).toBe("—");
    expect(formatSuppliesUnitLabel(null)).toBe("—");
  });

  it("builds options only from allowedUnits", () => {
    expect(buildSuppliesUnitOptions(["01"])).toEqual([
      { value: "01", label: "Santa Catarina (01)" },
    ]);
    expect(buildSuppliesUnitOptions(["02"])).toEqual([
      { value: "02", label: "Espírito Santo (02)" },
    ]);
    expect(buildSuppliesUnitOptions(["01", "02"]).map((o) => o.value)).toEqual([
      "01",
      "02",
    ]);
    expect(buildSuppliesUnitOptions(["01", "99"])).toEqual([
      { value: "01", label: "Santa Catarina (01)" },
      { value: "99", label: "Filial 99" },
    ]);
  });

  it("resolves default branch without inventing unauthorized units", () => {
    expect(resolveDefaultBranch(["01", "02"], "02")).toBe("02");
    expect(resolveDefaultBranch(["01"], "02")).toBe("01");
    expect(resolveDefaultBranch(["02"], "01")).toBe("02");
    expect(resolveDefaultBranch([], "01")).toBe("");
  });
});
