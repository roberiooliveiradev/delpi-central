import { describe, expect, it } from "vitest";

import {
  createCanvasTableBlock,
  parseComunicadoConfig,
  serializeComunicadoConfig,
} from "./comunicadoHelpers";

describe("canvas_table", () => {
  it("cria e normaliza dimensões e células sem virar bloco de dados", () => {
    const created = createCanvasTableBlock(30, 0);
    expect(created.rows).toBe(20);
    expect(created.cols).toBe(1);
    expect(created.cells).toHaveLength(20);

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
    expect(block.cells).toEqual([["A", "", ""], ["B", "C", "4"]]);
    expect(parsed.speakerNotes).toBe("Destacar o resultado.");

    const serialized = serializeComunicadoConfig(parsed);
    expect(serialized.speakerNotes).toBe("Destacar o resultado.");
    expect(serialized.blocks).toEqual([
      expect.objectContaining({ type: "canvas_table", rows: 2, cols: 3, cells: block.cells }),
    ]);
  });
});
