import { describe, expect, it } from "vitest";

import {
  applyCanvasTableDataRef,
  buildCanvasTableDataLinkPatch,
  canvasTableHasDataBinding,
  formatCanvasTableDataBindingLabel,
  listCanvasTableDataBindings,
  resolveCanvasTableCellDisplay,
} from "./canvasTableProjection";
import { normalizeCanvasTableCells } from "./comunicadoCanvasTable";
import type { ComunicadoCanvasTableBlock, ComunicadoDataResolved } from "./comunicadoTypes";

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

/** Meta + Realizado na mesma fonte (N dataRef / uma Grade). */
const multiFieldResolved: ComunicadoDataResolved = {
  kpiMetrics: [
    { field: "meta", value: 1400, label: "Meta" },
    { field: "value", value: 1146.3, label: "Realizado" },
  ],
};

function makeTable(rows: number, cols: number): ComunicadoCanvasTableBlock {
  return {
    id: "grade-test",
    type: "canvas_table",
    rows,
    cols,
    cells: normalizeCanvasTableCells([], rows, cols),
    headerRow: true,
    frame: { x: 10, y: 10, w: 40, h: 30 },
    style: { zIndex: 1 },
  };
}

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
    const block = makeTable(2, 2);
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
    const block = makeTable(3, 2);
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

  it("N dataRef na mesma Grade resolvem campos distintos", () => {
    const block = makeTable(3, 2);
    let next = applyCanvasTableDataRef(
      block,
      { row: 1, col: 1 },
      { field: "meta", format: "number", aggregation: "first" },
      "cell",
    );
    next = applyCanvasTableDataRef(
      next,
      { row: 2, col: 1 },
      { field: "value", format: "number", aggregation: "first" },
      "cell",
    );
    const meta = resolveCanvasTableCellDisplay(next.cells[1]![1]!, multiFieldResolved);
    const real = resolveCanvasTableCellDisplay(next.cells[2]![1]!, multiFieldResolved);
    expect(meta.fromData).toBe(true);
    expect(real.fromData).toBe(true);
    expect(meta.text).not.toBe(real.text);
    expect(meta.value).toBe(1400);
    expect(real.value).toBeCloseTo(1146.3);
  });

  it("applyCanvasTableDataRef cell não altera outro dataRef", () => {
    const block = makeTable(3, 2);
    let next = applyCanvasTableDataRef(
      block,
      { row: 1, col: 1 },
      { field: "meta", format: "number", aggregation: "first" },
      "cell",
    );
    next = applyCanvasTableDataRef(
      next,
      { row: 2, col: 1 },
      { field: "value", format: "number", aggregation: "first" },
      "cell",
    );
    expect(next.cells[1]?.[1]?.dataRef?.field).toBe("meta");
    expect(next.cells[2]?.[1]?.dataRef?.field).toBe("value");
  });

  it("buildCanvasTableDataLinkPatch não sobrescreve dataRef de outras células", () => {
    const block = makeTable(3, 2);
    const withMeta = applyCanvasTableDataRef(
      block,
      { row: 1, col: 1 },
      { field: "meta", format: "number", aggregation: "first" },
      "cell",
    );
    const patch = buildCanvasTableDataLinkPatch({
      dataSourceId: "src-ppm",
      resolved: multiFieldResolved,
      catalogFields: [
        { field: "meta", label: "Meta" },
        { field: "value", label: "Realizado" },
      ],
      targetCell: { row: 2, col: 1 },
      existingCells: withMeta.cells,
    });
    expect(patch.dataSourceId).toBe("src-ppm");
    expect(patch.cells?.[1]?.[1]?.dataRef?.field).toBe("meta");
    expect(patch.cells?.[2]?.[1]?.dataRef?.field).toBeTruthy();
  });

  it("listCanvasTableDataBindings lista todos os vínculos", () => {
    const block = makeTable(3, 2);
    let next = applyCanvasTableDataRef(
      block,
      { row: 1, col: 1 },
      { field: "meta", format: "number", aggregation: "first" },
      "cell",
    );
    next = applyCanvasTableDataRef(
      next,
      { row: 2, col: 1 },
      { field: "value", format: "number", aggregation: "avg" },
      "cell",
    );
    const bindings = listCanvasTableDataBindings(next);
    expect(bindings).toHaveLength(2);
    expect(bindings[0]).toMatchObject({ row: 1, col: 1, field: "meta", aggregation: "first" });
    expect(bindings[1]).toMatchObject({ row: 2, col: 1, field: "value", aggregation: "avg" });
    expect(formatCanvasTableDataBindingLabel(bindings[0]!)).toBe("2×2 · meta · first");
  });

  it("apply body respeita cabeçalho e não apaga escopo fora do corpo", () => {
    const block = makeTable(3, 2);
    const cells = block.cells.map((row, ri) =>
      row.map((cell, ci) =>
        ri === 0 && ci === 0
          ? { ...cell, kind: "text" as const, dataRef: { field: "meta", format: "raw" as const } }
          : cell,
      ),
    );
    const seeded = { ...block, cells, headerRow: true };
    const body = applyCanvasTableDataRef(
      seeded,
      { row: 1, col: 1 },
      { field: "value", format: "number", aggregation: "first" },
      "body",
    );
    expect(body.cells[0]?.[0]?.dataRef?.field).toBe("meta");
    expect(body.cells[1]?.[0]?.dataRef?.field).toBe("value");
    expect(body.cells[1]?.[1]?.dataRef?.field).toBe("value");
    expect(body.cells[2]?.[1]?.dataRef?.field).toBe("value");
  });
});
