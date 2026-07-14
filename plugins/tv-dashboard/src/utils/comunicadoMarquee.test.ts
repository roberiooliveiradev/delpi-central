import { describe, expect, it } from "vitest";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import { blocksInMarquee, normalizeMarqueeRect } from "./comunicadoMarquee";

describe("comunicadoMarquee", () => {
  it("normaliza retângulo independente da direção do arraste", () => {
    expect(normalizeMarqueeRect({ x1: 40, y1: 30, x2: 10, y2: 5 })).toEqual({
      x1: 10,
      y1: 5,
      x2: 40,
      y2: 30,
    });
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
});
