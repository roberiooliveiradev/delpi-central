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

  it("alinha dois grupos pelo bounding box sem colapsar filhos", () => {
    const a = createBlock("text", "A");
    const b = createBlock("text", "B");
    const c = createBlock("text", "C");
    const d = createBlock("text", "D");
    a.groupId = "g1";
    b.groupId = "g1";
    c.groupId = "g2";
    d.groupId = "g2";
    a.frame = { x: 0, y: 0, w: 10, h: 10 };
    b.frame = { x: 10, y: 10, w: 10, h: 10 };
    c.frame = { x: 40, y: 5, w: 10, h: 10 };
    d.frame = { x: 50, y: 15, w: 10, h: 10 };

    const next = alignComunicadoBlocks(
      [a, b, c, d],
      [a.id, b.id, c.id, d.id],
      "align-top",
    );
    const na = next.find((block) => block.id === a.id)!;
    const nb = next.find((block) => block.id === b.id)!;
    const nc = next.find((block) => block.id === c.id)!;
    const nd = next.find((block) => block.id === d.id)!;

    expect(nb.frame.x - na.frame.x).toBe(10);
    expect(nb.frame.y - na.frame.y).toBe(10);
    expect(nd.frame.x - nc.frame.x).toBe(10);
    expect(nd.frame.y - nc.frame.y).toBe(10);
    expect(na.frame.y).toBe(0);
    expect(nc.frame.y).toBe(0);
  });

  it("alinha ao slide com um bloco", () => {
    const a = createBlock("text", "A");
    a.frame = { x: 20, y: 30, w: 20, h: 10 };
    const next = alignComunicadoBlocks([a], [a.id], "align-slide-left");
    expect(next.find((block) => block.id === a.id)?.frame.x).toBe(0);
    const centered = alignComunicadoBlocks([a], [a.id], "align-slide-center-h");
    expect(centered.find((block) => block.id === a.id)?.frame.x).toBe(40);
  });
});
