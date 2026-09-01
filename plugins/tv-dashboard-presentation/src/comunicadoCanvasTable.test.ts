import { describe, expect, it } from "vitest";

import {
  createCanvasTableBlock,
  parseComunicadoConfig,
  serializeComunicadoConfig,
} from "./comunicadoHelpers";
import {
  CANVAS_TABLE_DEFAULT_FONT_SIZE,
  canvasTableCellsToStringMatrix,
  canvasTablePresetOptions,
  formatCanvasTableNumber,
  inferCanvasTableCellFromText,
  normalizeCanvasTableCell,
  normalizeCanvasTableCells,
  normalizeCanvasTableTrackSizes,
  applyCanvasTableTrackDrag,
  parseCanvasTableOptions,
  resolveCanvasTableFontSize,
  resolveCanvasTableRowHeightStyles,
  resolveCanvasTableCellBoxStyle,
  resolveCanvasTableGeometrySnapshot,
  commitCanvasTableCellText,
} from "./comunicadoCanvasTable";
import {
  applyComplexBlockFrameWithTypography,
  scaleComplexBlockOnResize,
} from "./scaleComplexBlockTypography";
import type { ComunicadoCanvasTableBlock } from "./comunicadoTypes";

describe("canvas_table", () => {
  it("cria e normaliza dimensões e células tipadas", () => {
    const created = createCanvasTableBlock(30, 0);
    expect(created.rows).toBe(20);
    expect(created.cols).toBe(1);
    expect(created.cells).toHaveLength(20);
    expect(created.cells[0]?.[0]).toEqual({ kind: "text", text: "" });
    expect(created.canvasTableOptions?.fontSize).toBe(CANVAS_TABLE_DEFAULT_FONT_SIZE);

    const parsed = parseComunicadoConfig({
      speakerNotes: "Destacar o resultado.",
      blocks: [{
        ...created,
        rows: 2,
        cols: 3,
        cells: [["A"], ["B", "C", 4]],
      }],
    });
    const block = parsed.blocks?.[0];
    expect(block?.type).toBe("canvas_table");
    if (block?.type !== "canvas_table") throw new Error("Bloco canvas_table esperado");
    expect(block.cells).toEqual([
      [
        { kind: "text", text: "A" },
        { kind: "text", text: "" },
        { kind: "text", text: "" },
      ],
      [
        { kind: "text", text: "B" },
        { kind: "text", text: "C" },
        { kind: "text", text: "4" },
      ],
    ]);
    expect(parsed.speakerNotes).toBe("Destacar o resultado.");

    const serialized = serializeComunicadoConfig(parsed);
    expect(serialized.speakerNotes).toBe("Destacar o resultado.");
    expect(serialized.blocks).toEqual([
      expect.objectContaining({ type: "canvas_table", rows: 2, cols: 3, cells: block.cells }),
    ]);
  });

  it("migra célula objeto number e serializa", () => {
    const cells = normalizeCanvasTableCells(
      [[{ kind: "number", value: 1400, format: "integer" }]],
      1,
      1,
    );
    expect(cells[0]?.[0]?.kind).toBe("number");
    expect(formatCanvasTableNumber(1400, "integer")).toBe("1.400");
    expect(formatCanvasTableNumber(41.7, "percent")).toBe("41,7%");
  });

  it("infere number e sparkline a partir do texto", () => {
    expect(inferCanvasTableCellFromText("1.400").kind).toBe("number");
    const spark = inferCanvasTableCellFromText("1 2 3 4 5 6");
    expect(spark.kind).toBe("sparkline");
    expect(spark.series?.length).toBe(6);
  });

  it("commit de texto preserva style, binding e format", () => {
    const painted = normalizeCanvasTableCell({
      kind: "text",
      text: "WEG",
      style: { backgroundColor: "#003366", color: "#fff", textAlign: "center" },
      dataRef: { field: "customer_name" },
      dataSourceId: "src-1",
    });
    const next = commitCanvasTableCellText(painted, "META WEG");
    expect(next.kind).toBe("text");
    expect(next.text).toBe("META WEG");
    expect(next.style).toEqual({
      backgroundColor: "#003366",
      color: "#fff",
      textAlign: "center",
    });
    expect(next.dataRef).toEqual({ field: "customer_name" });
    expect(next.dataSourceId).toBe("src-1");

    const numbered = normalizeCanvasTableCell({
      kind: "number",
      value: 10,
      format: "percent",
      style: { backgroundColor: "#111" },
      displayFormat: { category: "percent", decimalPlaces: 1 },
    });
    const asNumber = commitCanvasTableCellText(numbered, "42,5");
    expect(asNumber.kind).toBe("number");
    expect(asNumber.value).toBe(42.5);
    expect(asNumber.format).toBe("percent");
    expect(asNumber.style?.backgroundColor).toBe("#111");
    expect(asNumber.displayFormat).toEqual({ category: "percent", decimalPlaces: 1 });
  });

  it("presets de design aplicam banded/header/border", () => {
    expect(canvasTablePresetOptions("banded").bandedRows).toBe(true);
    expect(canvasTablePresetOptions("minimal").borderStyle).toBe("horizontal");
    expect(canvasTablePresetOptions("grid").headerStyle).toBe("subtle");
  });

  it("resize do bloco escala fontSize da grade (paridade KPI)", () => {
    const block = createCanvasTableBlock(3, 3) as ComunicadoCanvasTableBlock;
    expect(resolveCanvasTableFontSize(block)).toBe(18);
    const grown = applyComplexBlockFrameWithTypography(block, {
      ...block.frame,
      w: block.frame.w * 2,
      h: block.frame.h * 2,
    }) as ComunicadoCanvasTableBlock;
    expect(grown.canvasTableOptions?.fontSize).toBe(36);
    expect(grown.style?.fontSize).toBe(36);
    const doubled = scaleComplexBlockOnResize(grown, block.frame, {
      ...block.frame,
      w: block.frame.w * 2,
      h: block.frame.h * 2,
    }) as ComunicadoCanvasTableBlock;
    expect(doubled.canvasTableOptions?.fontSize).toBe(72);
  });

  it("canvasTableCellsToStringMatrix usa texto formatado", () => {
    const matrix = canvasTableCellsToStringMatrix([
      [{ kind: "number", value: 12.5, format: "decimal" }],
    ]);
    expect(matrix[0]?.[0]).toBe("12,5");
  });

  it("normalizeCanvasTableCell aceita string legado", () => {
    expect(normalizeCanvasTableCell("ok")).toEqual({ kind: "text", text: "ok" });
  });

  it("parse e serialize preservam rowHeights; slide sem o campo fica inalterado", () => {
    const created = createCanvasTableBlock(30, 0);
    const parsedWithHeights = parseComunicadoConfig({
      blocks: [
        {
          ...created,
          rows: 3,
          cols: 1,
          cells: [["A"], ["B"], ["C"]],
          canvasTableOptions: { rowHeights: [20, 20, 60] },
        },
      ],
    });
    const withHeights = parsedWithHeights.blocks?.[0];
    expect(withHeights?.type).toBe("canvas_table");
    if (withHeights?.type !== "canvas_table") throw new Error("canvas_table");
    expect(withHeights.canvasTableOptions?.rowHeights).toEqual([20, 20, 60]);
    const serialized = serializeComunicadoConfig(parsedWithHeights);
    const serializedBlock = serialized.blocks?.[0] as { canvasTableOptions?: { rowHeights?: number[] } };
    expect(serializedBlock.canvasTableOptions?.rowHeights).toEqual([20, 20, 60]);

    const parsedPlain = parseComunicadoConfig({
      blocks: [{ ...created, rows: 2, cols: 1, cells: [["A"], ["B"]] }],
    });
    const plain = parsedPlain.blocks?.[0];
    expect(plain?.type).toBe("canvas_table");
    if (plain?.type !== "canvas_table") throw new Error("canvas_table");
    expect(plain.canvasTableOptions?.rowHeights).toBeUndefined();
    expect(parseCanvasTableOptions({ fontSize: 18 })?.rowHeights).toBeUndefined();
  });

  it("normalizeCanvasTableTrackSizes soma 100 e aplica mínimo", () => {
    const even = normalizeCanvasTableTrackSizes(undefined, 4);
    expect(even).toHaveLength(4);
    expect(even.reduce((sum, item) => sum + item, 0)).toBeCloseTo(100, 5);
    even.forEach((item) => expect(item).toBeCloseTo(25, 5));

    const skewed = normalizeCanvasTableTrackSizes([20, 20, 60], 3);
    expect(skewed).toEqual([20, 20, 60]);
    expect(skewed.reduce((sum, item) => sum + item, 0)).toBeCloseTo(100, 5);

    const tiny = normalizeCanvasTableTrackSizes([1, 99], 2);
    expect(tiny[0]).toBeGreaterThanOrEqual(4);
    expect(tiny.reduce((sum, item) => sum + item, 0)).toBeCloseTo(100, 5);
  });

  it("applyCanvasTableTrackDrag transfere delta, clampa e soma 100", () => {
    const moved = applyCanvasTableTrackDrag({ tracks: [25, 25, 25, 25], index: 0, deltaPct: 10 });
    expect(moved[0]).toBeCloseTo(35, 5);
    expect(moved[1]).toBeCloseTo(15, 5);
    expect(moved[2]).toBeCloseTo(25, 5);
    expect(moved.reduce((sum, item) => sum + item, 0)).toBeCloseTo(100, 5);

    const clamped = applyCanvasTableTrackDrag({ tracks: [10, 90], index: 0, deltaPct: 100 });
    expect(clamped[0]).toBeGreaterThanOrEqual(4);
    expect(clamped[1]).toBeGreaterThanOrEqual(4);
    expect(clamped.reduce((sum, item) => sum + item, 0)).toBeCloseTo(100, 5);

    const lastAbsorbs = applyCanvasTableTrackDrag({ tracks: [50, 50], index: 0, deltaPct: -20 });
    expect(lastAbsorbs[0]).toBeCloseTo(30, 5);
    expect(lastAbsorbs[1]).toBeCloseTo(70, 5);

    expect(applyCanvasTableTrackDrag({ tracks: [40, 60], index: 1, deltaPct: 10 })).toEqual(
      normalizeCanvasTableTrackSizes([40, 60], 2),
    );
  });

  it("resolveCanvasTableRowHeightStyles aplica % só quando o length bate com rows", () => {
    expect(resolveCanvasTableRowHeightStyles([20, 20, 60], 3)).toEqual([
      { height: "20%" },
      { height: "20%" },
      { height: "60%" },
    ]);
    expect(resolveCanvasTableRowHeightStyles([20, 80], 3)).toEqual([
      undefined,
      undefined,
      undefined,
    ]);
    expect(resolveCanvasTableRowHeightStyles(undefined, 2)).toEqual([undefined, undefined]);
  });

  it("geometria e fill da célula não dependem de editable", () => {
    const block = {
      rows: 2,
      cols: 2,
      merges: [{ row: 0, col: 0, rowspan: 1, colspan: 2 }],
      cells: [
        [
          { kind: "text" as const, text: "A", style: { backgroundColor: "#003366" } },
          { kind: "text" as const, text: "B" },
        ],
        [{ kind: "text" as const, text: "C" }, { kind: "text" as const, text: "D" }],
      ],
      canvasTableOptions: {
        columnWidths: [40, 60],
        rowHeights: [30, 70],
      },
    };
    const snapA = resolveCanvasTableGeometrySnapshot(block);
    const snapB = resolveCanvasTableGeometrySnapshot(block);
    expect(snapA).toEqual(snapB);
    expect(snapA.columnWidths).toEqual([40, 60]);
    expect(snapA.rowHeights).toEqual([30, 70]);
    expect(snapA.merges).toEqual([{ row: 0, col: 0, rowspan: 1, colspan: 2 }]);
    expect(snapA.cellBackgrounds[0]).toBe("#003366");
    expect(
      resolveCanvasTableCellBoxStyle({
        kind: "text",
        text: "A",
        style: { backgroundColor: "#003366", textAlign: "center" },
      }),
    ).toEqual({ backgroundColor: "#003366", textAlign: "center" });
  });
});
