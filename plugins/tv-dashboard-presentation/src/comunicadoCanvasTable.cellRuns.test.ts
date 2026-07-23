import { describe, expect, it } from "vitest";

import {
  canvasTableCellDisplayRuns,
  normalizeCanvasTableCell,
} from "./comunicadoCanvasTable";

describe("canvas_table contentRuns", () => {
  it("normaliza contentRuns na célula", () => {
    const cell = normalizeCanvasTableCell({
      kind: "text",
      text: "Meta 1.400",
      contentRuns: [
        { text: "Meta", style: { fontWeight: "bold" } },
        { text: " 1.400" },
      ],
    });
    expect(cell.contentRuns).toHaveLength(2);
  });

  it("sem runs usa estilo monolítico como run implícito", () => {
    const runs = canvasTableCellDisplayRuns(
      { kind: "text", text: "Olá", style: { color: "#123456", fontWeight: 700 } },
      "Olá",
    );
    expect(runs).toHaveLength(1);
    expect(runs[0]?.style?.color).toBe("#123456");
    expect(runs[0]?.style?.fontWeight).toBe("bold");
  });
});
