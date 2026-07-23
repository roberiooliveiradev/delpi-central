import { describe, expect, it } from "vitest";

import {
  applyCanvasTableDataRef,
  buildCanvasTableDataLinkPatch,
  canvasTableHasDataBinding,
  resolveCanvasTableCellDisplay,
} from "./canvasTableProjection";
import { createCanvasTableBlock } from "./comunicadoHelpers";
import type { ComunicadoDataResolved } from "./comunicadoTypes";

const resolved: ComunicadoDataResolved = {
  kpi: { value: 42, label: "ROL" },
  table: {
    columns: ["rol", "mes"],
    rows: [
      { rol: 10, mes: "Jan" },
      { rol: 20, mes: "Fev" },
      { rol: 30, mes: "Mar" },
      { rol: 40, mes: "Abr" },
      { rol: 50, mes: "Mai" },
      { rol: 60, mes: "Jun" },
    ],
  },
};

describe("canvasTableProjection", () => {
  it("resolveCanvasTableCellDisplay usa dataRef + resolved", () => {
    const display = resolveCanvasTableCellDisplay(
      { kind: "number", dataRef: { field: "rol", aggregation: "avg", format: "number" } },
      resolved,
    );
    expect(display.fromData).toBe(true);
    expect(display.text).not.toBe("—");
  });

  it("sparkline com aggregation list monta série", () => {
    const display = resolveCanvasTableCellDisplay(
      {
        kind: "sparkline",
        dataRef: { field: "rol", aggregation: "list", format: "number" },
      },
      resolved,
    );
    expect(display.series?.length).toBeGreaterThanOrEqual(5);
    expect(display.value).toBe(60);
  });

  it("buildCanvasTableDataLinkPatch liga fonte e sugere dataRef na célula", () => {
    const block = createCanvasTableBlock(2, 2);
    const patch = buildCanvasTableDataLinkPatch({
      dataSourceId: "src-1",
      resolved,
      targetCell: { row: 1, col: 0 },
      existingCells: block.cells,
    });
    expect(patch.dataSourceId).toBe("src-1");
    expect(patch.cells?.[1]?.[0]?.dataRef?.field).toBeTruthy();
  });

  it("applyCanvasTableDataRef aplica à coluna (multi-célula)", () => {
    const block = createCanvasTableBlock(3, 2);
    const withRef = applyCanvasTableDataRef(
      block,
      { row: 1, col: 0 },
      { field: "rol", format: "number", aggregation: "first" },
      "column",
    );
    expect(withRef.cells[0]?.[0]?.dataRef).toBeUndefined(); // cabeçalho
    expect(withRef.cells[1]?.[0]?.dataRef?.field).toBe("rol");
    expect(withRef.cells[2]?.[0]?.dataRef?.field).toBe("rol");
    expect(withRef.cells[1]?.[1]?.dataRef).toBeUndefined();
    expect(canvasTableHasDataBinding(withRef)).toBe(true);
  });
});
