import { describe, expect, it } from "vitest";
import type { ComunicadoBlock, ComunicadoFrame } from "@delpi/tv-dashboard-presentation";

import { finalizeMultiFramesWithSnap } from "./finalizeMultiFramesWithSnap";

function block(id: string, frame: ComunicadoFrame, groupId?: string): ComunicadoBlock {
  return {
    id,
    type: "shape",
    shape: "rect",
    frame,
    ...(groupId ? { groupId } : {}),
  } as ComunicadoBlock;
}

describe("finalizeMultiFramesWithSnap", () => {
  it("mantém o ponto exato perto das bordas quando grade e imãs estão desligados", () => {
    const target = { x: 0.27, y: 0.13, w: 24, h: 11 };
    const current = block("free", target);
    const next = finalizeMultiFramesWithSnap({
      blocks: [current],
      ids: ["free"],
      primaryId: "free",
      startFrames: new Map([["free", { x: 20, y: 20, w: 24, h: 11 }]]),
      currentById: new Map([["free", target]]),
      mode: "move",
      snapToGrid: false,
    });
    expect(next.get("free")).toEqual(target);
  });

  it("preserva coordenadas livres negativas no pasteboard", () => {
    const target = { x: -3.25, y: -0.75, w: 18, h: 8 };
    const current = block("free", target);
    const next = finalizeMultiFramesWithSnap({
      blocks: [current],
      ids: ["free"],
      primaryId: "free",
      startFrames: new Map([["free", { x: 10, y: 10, w: 18, h: 8 }]]),
      currentById: new Map([["free", target]]),
      mode: "move",
      snapToGrid: false,
    });
    expect(next.get("free")).toEqual(target);
  });

  it("preserva delta relativo ao encaixar o primário na grade", () => {
    const a = block("a", { x: 11, y: 11, w: 10, h: 10 }, "g1");
    const b = block("b", { x: 31, y: 21, w: 10, h: 10 }, "g1");
    const startFrames = new Map<string, ComunicadoFrame>([
      ["a", { x: 10, y: 10, w: 10, h: 10 }],
      ["b", { x: 30, y: 20, w: 10, h: 10 }],
    ]);
    const currentById = new Map<string, ComunicadoFrame>([
      ["a", { x: 11, y: 11, w: 10, h: 10 }],
      ["b", { x: 31, y: 21, w: 10, h: 10 }],
    ]);

    const next = finalizeMultiFramesWithSnap({
      blocks: [a, b],
      ids: ["a", "b"],
      primaryId: "a",
      startFrames,
      currentById,
      mode: "move",
      snapToGrid: true,
      snapPercents: { xPercent: 5, yPercent: 5 },
    });

    expect(next.get("a")).toEqual({ x: 10, y: 10, w: 10, h: 10 });
    expect(next.get("b")).toEqual({ x: 30, y: 20, w: 10, h: 10 });
  });

  it("não desloca irmãos quando o primário já está na grade", () => {
    const a = block("a", { x: 10, y: 10, w: 10, h: 10 }, "g1");
    const b = block("b", { x: 30, y: 20, w: 10, h: 10 }, "g1");
    const frames = new Map<string, ComunicadoFrame>([
      ["a", { x: 10, y: 10, w: 10, h: 10 }],
      ["b", { x: 30, y: 20, w: 10, h: 10 }],
    ]);
    const next = finalizeMultiFramesWithSnap({
      blocks: [a, b],
      ids: ["a", "b"],
      primaryId: "a",
      startFrames: frames,
      currentById: frames,
      mode: "move",
      snapToGrid: true,
      snapPercents: { xPercent: 5, yPercent: 5 },
    });
    expect(next.get("a")).toEqual({ x: 10, y: 10, w: 10, h: 10 });
    expect(next.get("b")).toEqual({ x: 30, y: 20, w: 10, h: 10 });
  });
});
