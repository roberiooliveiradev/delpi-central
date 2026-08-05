import { describe, expect, it } from "vitest";
import {
  buildCreateSummary,
  filterCostCenters,
  validateValidityRange,
} from "./responsibilities";

describe("responsibilities utils", () => {
  it("monta resumo de amarração com dados reais", () => {
    const text = buildCreateSummary({
      userName: "Maria da Silva",
      costCenterLabel: "1234 – Produção",
      exerciseYear: 2027,
      type: "owner",
    });
    expect(text).toContain("Maria da Silva");
    expect(text).toContain("1234 – Produção");
    expect(text).toContain("2027");
    expect(text).toMatch(/responsável/i);
  });

  it("valida período inválido", () => {
    expect(validateValidityRange("2026-12-01", "2026-01-01")).toMatch(/não pode ser anterior/i);
    expect(validateValidityRange("2026-01-01", "2026-12-01")).toBeNull();
  });

  it("encadeia centros de custo por unidade e área", () => {
    const catalog = {
      units: [{ code: "01", name: "SC" }],
      areas: [{ code: "PROD", name: "Produção", unit_code: "01" }],
      cost_centers: [
        { code: "205", name: "TI", branch: "01", unit_code: "01", area_code: "PROD" },
        { code: "205", name: "TI ES", branch: "02", unit_code: "02", area_code: "X" },
        { code: "999", name: "Outro", branch: "02", unit_code: "02", area_code: "X" },
      ],
    };
    const filtered = filterCostCenters(catalog, "01", "PROD");
    expect(filtered.map((c) => c.code)).toEqual(["205"]);
    expect(filterCostCenters(catalog, "02", "").map((c) => c.code).sort()).toEqual([
      "205",
      "999",
    ]);
  });
});
