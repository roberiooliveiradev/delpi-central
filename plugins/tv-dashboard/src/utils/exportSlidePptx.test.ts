import { describe, expect, it } from "vitest";
import { createCanvasTableBlock, createChartViewBlock } from "@delpi/tv-dashboard-presentation";

import { mapComunicadoBlocksToPptxElements } from "./exportSlidePptx";

describe("mapComunicadoBlocksToPptxElements", () => {
  it("mapeia grade estática e degrada gráfico complexo para placeholder", () => {
    const table = createCanvasTableBlock(2, 2);
    table.cells = [["Produto", "Qtd."], ["ABC", "4"]];
    const chart = createChartViewBlock("line");

    const elements = mapComunicadoBlocksToPptxElements([table, chart]);

    expect(elements[0]).toMatchObject({
      kind: "table",
      rows: table.cells,
      headerRow: true,
    });
    expect(elements[1]).toMatchObject({ kind: "placeholder", text: "[Gráfico]" });
  });
});
