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
  resolveCanvasTableFontSize,
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
  });

  it("infere number e sparkline a partir do texto", () => {
    expect(inferCanvasTableCellFromText("1.400").kind).toBe("number");
    const spark = inferCanvasTableCellFromText("1 2 3 4 5 6");
    expect(spark.kind).toBe("sparkline");
    expect(spark.series?.length).toBe(6);
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
});
