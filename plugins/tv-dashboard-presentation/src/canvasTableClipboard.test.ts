import { describe, expect, it } from "vitest";

import {
  canvasTableClipboardToTsv,
  clearCanvasTableCellContent,
  clearCanvasTableCellsContent,
  parseCanvasTableClipboardTsv,
  pasteCanvasTableClipboard,
  serializeCanvasTableClipboard,
} from "./canvasTableClipboard";
import { normalizeCanvasTableCell } from "./comunicadoCanvasTable";

describe("canvasTableClipboard", () => {
  it("Delete limpa conteúdo e mantém backgroundColor / dataRef", () => {
    const painted = normalizeCanvasTableCell({
      kind: "text",
      text: "WEG",
      style: { backgroundColor: "#003366" },
      dataRef: { field: "customer_name" },
    });
    const cleared = clearCanvasTableCellContent(painted);
    expect(cleared.text).toBe("");
    expect(cleared.style?.backgroundColor).toBe("#003366");
    expect(cleared.dataRef).toEqual({ field: "customer_name" });
  });

  it("serializa retângulo e cola no destino", () => {
    const grid = [
      [
        normalizeCanvasTableCell({ kind: "text", text: "A", style: { color: "#111" } }),
        normalizeCanvasTableCell("B"),
      ],
      [normalizeCanvasTableCell("C"), normalizeCanvasTableCell("D")],
    ];
    const payload = serializeCanvasTableClipboard({
      cells: grid,
      selected: [
        { row: 0, col: 0 },
        { row: 0, col: 1 },
      ],
    });
    expect(payload?.rows).toBe(1);
    expect(payload?.cols).toBe(2);
    expect(canvasTableClipboardToTsv(payload!)).toBe("A\tB");

    const pasted = pasteCanvasTableClipboard({
      cells: [
        [normalizeCanvasTableCell(""), normalizeCanvasTableCell("")],
        [normalizeCanvasTableCell(""), normalizeCanvasTableCell("")],
      ],
      payload: payload!,
      origin: { row: 1, col: 0 },
      rows: 2,
      cols: 2,
    });
    expect(pasted.cells[1]?.[0]?.text).toBe("A");
    expect(pasted.cells[1]?.[0]?.style?.color).toBe("#111");
    expect(pasted.cells[1]?.[1]?.text).toBe("B");
  });

  it("parseia TSV externo", () => {
    const payload = parseCanvasTableClipboardTsv("1\t2\n3\t4");
    expect(payload?.rows).toBe(2);
    expect(payload?.cols).toBe(2);
    expect(payload?.cells[0]?.[0]?.text).toBe("1");
  });

  it("clearCanvasTableCellsContent zera várias células", () => {
    const grid = [
      [
        normalizeCanvasTableCell({
          kind: "text",
          text: "A",
          style: { backgroundColor: "#fff" },
        }),
        normalizeCanvasTableCell("B"),
      ],
    ];
    const next = clearCanvasTableCellsContent(grid, [
      { row: 0, col: 0 },
      { row: 0, col: 1 },
    ]);
    expect(next[0]?.[0]?.text).toBe("");
    expect(next[0]?.[0]?.style?.backgroundColor).toBe("#fff");
    expect(next[0]?.[1]?.text).toBe("");
  });
});
