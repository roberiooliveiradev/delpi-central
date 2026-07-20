import { describe, expect, it } from "vitest";

import {
  ANALYSIS_STATUS_HEADER_HINT,
  SAFETY_STOCK_STATUS_LABELS,
  analysisQualityWarningLabel,
  safetyStockStatusLabel,
  safetyStockStatusVariant,
  stockProjectionLabel,
  stockProjectionVariant,
  unitSuffix,
} from "./safetyStockStatus";

describe("safetyStockStatus", () => {
  it("mapeia labels em português", () => {
    expect(safetyStockStatusLabel("below_safety_stock")).toBe(
      SAFETY_STOCK_STATUS_LABELS.below_safety_stock,
    );
    expect(safetyStockStatusLabel("without_safety_stock")).toContain("Sem estoque");
  });

  it("define variantes semânticas por status", () => {
    expect(safetyStockStatusVariant("below_safety_stock")).toBe("danger");
    expect(safetyStockStatusVariant("at_safety_stock")).toBe("info");
    expect(safetyStockStatusVariant("above_safety_stock")).toBe("success");
  });

  it("mapeia status da projeção cronológica", () => {
    expect(stockProjectionLabel("temporary_shortage")).toContain("temporária");
    expect(stockProjectionVariant("projected_deficit")).toBe("danger");
    expect(stockProjectionVariant("sufficient")).toBe("success");
  });

  it("não mistura sufixos de unidade no agrupamento visual", () => {
    expect(unitSuffix("PC")).toBe("unidades");
    expect(unitSuffix("MT")).toBe("metros");
    expect(unitSuffix("KG")).toBe("quilos");
  });

  it("explica situação da análise e alertas em português", () => {
    expect(ANALYSIS_STATUS_HEADER_HINT).toContain("Abaixo do sugerido");
    expect(ANALYSIS_STATUS_HEADER_HINT).toContain("Adequado");
    expect(analysisQualityWarningLabel("lead_time_missing_or_zero")).toContain(
      "lead time",
    );
  });
});
