import { describe, expect, it } from "vitest";

import { singleCanvasTableCellSelection } from "./canvasTableCellSelection";
import { resolveStageHasPartSelection } from "./stagePartSelection";

describe("resolveStageHasPartSelection", () => {
  it("inclui célula da Grade como filho (Esc → clear-parts)", () => {
    expect(
      resolveStageHasPartSelection({
        selectedCanvasTableCell: singleCanvasTableCellSelection("g1", 0, 0),
      }),
    ).toBe(true);
  });

  it("sem filhos retorna false", () => {
    expect(resolveStageHasPartSelection({})).toBe(false);
  });

  it("parte KPI também conta", () => {
    expect(
      resolveStageHasPartSelection({
        selectedKpiPart: { kind: "title" },
      }),
    ).toBe(true);
  });
});
