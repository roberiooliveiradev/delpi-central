import { describe, expect, it } from "vitest";

import {
  peerFramesForSmartGuides,
  snapFrameToPeerBlocks,
} from "./comunicadoSmartGuides";

describe("comunicadoSmartGuides", () => {
  it("encaixa bordas esquerdas no move e emite guia vertical", () => {
    const peer = { x: 10, y: 20, w: 30, h: 15 };
    const frame = { x: 10.5, y: 40, w: 20, h: 10 };
    const { frame: snapped, guides } = snapFrameToPeerBlocks(frame, [peer], "move");
    expect(snapped.x).toBe(10);
    expect(snapped.y).toBe(40);
    expect(guides).toEqual([{ orientation: "v", position: 10 }]);
  });

  it("encaixa centros horizontais", () => {
    const peer = { x: 10, y: 10, w: 40, h: 20 }; // cx = 30
    const frame = { x: 20.4, y: 50, w: 20, h: 10 }; // cx = 30.4
    const { frame: snapped, guides } = snapFrameToPeerBlocks(frame, [peer], "move");
    expect(snapped.x).toBeCloseTo(20, 5);
    expect(guides.some((g) => g.orientation === "v" && g.position === 30)).toBe(true);
  });

  it("encaixa borda direita no resize mantendo a esquerda", () => {
    const peer = { x: 0, y: 0, w: 50, h: 10 }; // right = 50
    const frame = { x: 10, y: 20, w: 39.5, h: 12 };
    const { frame: snapped, guides } = snapFrameToPeerBlocks(frame, [peer], "resize");
    expect(snapped.x).toBe(10);
    expect(snapped.w).toBe(40);
    expect(guides).toContainEqual({ orientation: "v", position: 50 });
  });

  it("não encaixa fora do limiar", () => {
    const peer = { x: 10, y: 10, w: 20, h: 20 };
    const frame = { x: 50, y: 50, w: 10, h: 10 };
    const { frame: snapped, guides } = snapFrameToPeerBlocks(frame, [peer], "move", 0.5);
    expect(snapped).toEqual(frame);
    expect(guides).toEqual([]);
  });

  it("peerFramesForSmartGuides exclui ids arrastados", () => {
    const blocks = [
      { id: "a", frame: { x: 0, y: 0, w: 10, h: 10 } },
      { id: "b", frame: { x: 20, y: 0, w: 10, h: 10 } },
    ];
    expect(peerFramesForSmartGuides(blocks, new Set(["a"]))).toEqual([blocks[1].frame]);
  });
});
