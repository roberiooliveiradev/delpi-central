import { describe, expect, it } from "vitest";
import { createCanvasTableBlock, createChartViewBlock } from "@delpi/tv-dashboard-presentation";
import type { ComunicadoMediaBlock } from "@delpi/tv-dashboard-presentation";

import { mapComunicadoBlocksToPptxElements } from "./exportSlidePptxElements";

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

  it("exporta vídeo como placeholder (sem stream no PPTX)", () => {
    const video = {
      id: "v1",
      type: "video",
      assetId: "vid-1",
      frame: { x: 0, y: 0, w: 40, h: 40 },
      style: {},
    } as ComunicadoMediaBlock;
    const elements = mapComunicadoBlocksToPptxElements([video]);
    expect(elements).toEqual([
      expect.objectContaining({ kind: "placeholder", text: "[Vídeo]", block: video }),
    ]);
  });
});
