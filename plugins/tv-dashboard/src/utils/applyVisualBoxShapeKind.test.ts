import { createBlock } from "@delpi/tv-dashboard-presentation";
import { describe, expect, it } from "vitest";

import { buildVisualBoxShapeKindPatch } from "./applyVisualBoxShapeKind";

describe("buildVisualBoxShapeKindPatch", () => {
  it("troca kind mantendo frame quando o primitivo é o mesmo", () => {
    const block = createBlock("shape");
    block.shape = "rectangle";
    block.frame = { x: 20, y: 30, w: 15, h: 12 };
    const patch = buildVisualBoxShapeKindPatch(block, "roundedRectangle");
    expect(patch).toEqual({ shape: "roundedRectangle" });
  });

  it("recalcula frame ao mudar primitivo e ancora na origem (com clamp)", () => {
    const block = createBlock("shape");
    block.shape = "rectangle";
    block.frame = { x: 10, y: 12, w: 20, h: 20 };
    const patch = buildVisualBoxShapeKindPatch(block, "line");
    expect(patch?.shape).toBe("line");
    expect(patch?.frame).toBeDefined();
    expect(patch?.frame?.x).toBe(10);
    expect(patch?.frame?.y).toBe(12);
    expect(patch?.frame?.w).not.toBe(20);
  });

  it("ignora bloco que não é visual box", () => {
    const image = createBlock("image");
    expect(buildVisualBoxShapeKindPatch(image, "rectangle")).toBeNull();
  });
});
