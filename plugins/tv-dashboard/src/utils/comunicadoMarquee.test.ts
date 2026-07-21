import { describe, expect, it } from "vitest";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import {
  blocksInMarquee,
  mergeMarqueeSelection,
  normalizeMarqueeRect,
  resolveMarqueeIntent,
  subtractMarqueeSelection,
} from "./comunicadoMarquee";

describe("comunicadoMarquee", () => {
  it("normaliza retângulo independente da direção do arraste", () => {
    expect(normalizeMarqueeRect({ x1: 40, y1: 30, x2: 10, y2: 5 })).toEqual({
      x1: 10,
      y1: 5,
      x2: 40,
      y2: 30,
    });
  });

  it("L→R seleciona; R→L remove", () => {
    expect(resolveMarqueeIntent({ x1: 10, y1: 10, x2: 40, y2: 20 })).toBe("add");
    expect(resolveMarqueeIntent({ x1: 40, y1: 10, x2: 10, y2: 20 })).toBe("subtract");
    expect(resolveMarqueeIntent({ x1: 10, y1: 40, x2: 10, y2: 10 })).toBe("add");
  });

  it("merge e subtract de seleção", () => {
    expect(mergeMarqueeSelection(["a"], ["b", "a"])).toEqual(["a", "b"]);
    expect(subtractMarqueeSelection(["a", "b", "c"], ["b"])).toEqual(["a", "c"]);
  });

  it("lista blocos cuja moldura intersecta a caixa", () => {
    const blocks: ComunicadoBlock[] = [
      { id: "a", type: "text", content: "A", frame: { x: 0, y: 0, w: 20, h: 20 } },
      { id: "b", type: "text", content: "B", frame: { x: 50, y: 50, w: 20, h: 20 } },
      { id: "c", type: "text", content: "C", frame: { x: 15, y: 15, w: 10, h: 10 } },
    ];
    expect(blocksInMarquee(blocks, { x1: 0, y1: 0, x2: 25, y2: 25 })).toEqual(["a", "c"]);
    expect(blocksInMarquee(blocks, { x1: 60, y1: 60, x2: 80, y2: 80 })).toEqual(["b"]);
    expect(blocksInMarquee(blocks, { x1: 90, y1: 90, x2: 99, y2: 99 })).toEqual([]);
  });

  it("ignora fonte de dados oculta (vinculada) no marquee", () => {
    const blocks: ComunicadoBlock[] = [
      {
        id: "src-1",
        type: "data_source",
        frame: { x: 0, y: 0, w: 20, h: 20 },
        dataBinding: { operationId: "get_oee", params: {} },
      },
      {
        id: "chart-1",
        type: "chart_view",
        chartType: "line",
        dataSourceId: "src-1",
        frame: { x: 0, y: 0, w: 20, h: 20 },
      },
    ];
    expect(blocksInMarquee(blocks, { x1: 0, y1: 0, x2: 25, y2: 25 })).toEqual(["chart-1"]);
  });
});
