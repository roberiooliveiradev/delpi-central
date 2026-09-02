import { describe, expect, it } from "vitest";

import {
  resolveCanvasTablePasteOrigin,
  shouldRoutePasteToCanvasTable,
} from "./canvasTablePasteRoute";

describe("canvasTablePasteRoute", () => {
  it("célula ativa + sem editingText → rota Grade", () => {
    expect(
      shouldRoutePasteToCanvasTable({
        selectedCanvasTableCell: {
          blockId: "t1",
          cells: [{ row: 0, col: 1 }],
          focus: { row: 0, col: 1 },
        },
        editingTextId: null,
      }),
    ).toBe(true);
  });

  it("sem célula → external (TSV→bloco)", () => {
    expect(
      shouldRoutePasteToCanvasTable({
        selectedCanvasTableCell: null,
        editingTextId: null,
      }),
    ).toBe(false);
    expect(
      shouldRoutePasteToCanvasTable({
        selectedCanvasTableCell: { blockId: "t1", cells: [] },
      }),
    ).toBe(false);
  });

  it("editingTextId ativo → não intercepta", () => {
    expect(
      shouldRoutePasteToCanvasTable({
        selectedCanvasTableCell: {
          blockId: "t1",
          cells: [{ row: 0, col: 0 }],
        },
        editingTextId: "text-1",
      }),
    ).toBe(false);
  });

  it("resolveCanvasTablePasteOrigin prefer focus", () => {
    expect(
      resolveCanvasTablePasteOrigin({
        blockId: "t1",
        cells: [
          { row: 1, col: 1 },
          { row: 0, col: 0 },
        ],
        focus: { row: 2, col: 3 },
      }),
    ).toEqual({ row: 2, col: 3 });
  });
});
