import { describe, expect, it } from "vitest";

import { createBlock } from "@delpi/tv-dashboard-presentation";

import { alignComunicadoBlocks } from "./comunicadoLayoutAlign";

describe("alignComunicadoBlocks", () => {
  it("alinha bordas esquerda", () => {
    const a = createBlock("text", "A");
    a.frame = { x: 10, y: 10, w: 20, h: 10 };
    const b = createBlock("text", "B");
    b.frame = { x: 40, y: 20, w: 20, h: 10 };
    const next = alignComunicadoBlocks([a, b], [a.id, b.id], "align-left");
    expect(next.find((block) => block.id === b.id)?.frame.x).toBe(10);
  });

  it("distribui horizontalmente com 3 blocos", () => {
    const blocks = [0, 30, 60].map((x, index) => {
      const block = createBlock("text", String(index));
      block.frame = { x, y: 10, w: 10, h: 10 };
      return block;
    });
    const next = alignComunicadoBlocks(
      blocks,
      blocks.map((block) => block.id),
      "distribute-h",
    );
    const xs = next.map((block) => block.frame.x);
    expect(xs[1] - xs[0]).toBeCloseTo(xs[2] - xs[1], 1);
  });
});
