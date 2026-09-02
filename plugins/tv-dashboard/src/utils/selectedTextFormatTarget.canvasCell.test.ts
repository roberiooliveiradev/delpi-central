import { describe, expect, it } from "vitest";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import { resolveSelectedTextFormatTarget } from "./selectedTextFormatTarget";

const canvasTable = {
  id: "ct1",
  type: "canvas_table",
  frame: { x: 0, y: 0, w: 30, h: 20 },
  rows: 2,
  cols: 2,
  cells: [
    [
      { kind: "text", text: "A", style: { fontWeight: "700", fontSize: 18 } },
      { kind: "text", text: "B" },
    ],
    [{ kind: "text", text: "C" }, { kind: "text", text: "D" }],
  ],
  canvasTableOptions: { fontSize: 14 },
} as ComunicadoBlock;

describe("resolveSelectedTextFormatTarget canvasCell", () => {
  it("célula ativa → canvasCell com estilo da célula", () => {
    const target = resolveSelectedTextFormatTarget({
      selected: canvasTable,
      selectedCanvasTableCell: {
        blockId: "ct1",
        cells: [{ row: 0, col: 0 }],
        focus: { row: 0, col: 0 },
      },
    });
    expect(target?.mode).toBe("canvasCell");
    if (target?.mode === "canvasCell") {
      expect(target.style.fontWeight).toBe("700");
      expect(target.style.fontSize).toBe(18);
      expect(target.focus).toEqual({ row: 0, col: 0 });
    }
  });

  it("sem célula → complexGlobal", () => {
    expect(resolveSelectedTextFormatTarget({ selected: canvasTable })?.mode).toBe(
      "complexGlobal",
    );
  });
});
