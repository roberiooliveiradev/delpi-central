import { describe, expect, it } from "vitest";

import {
  adjustEdgeLabelPosition,
  computeEdgePathOffsets,
} from "./diagramEdgeRouting";

describe("computeEdgePathOffsets", () => {
  it("espalha conexões que saem do mesmo nó", () => {
    const offsets = computeEdgePathOffsets([
      { id: "e1", source: "g1", target: "a" },
      { id: "e2", source: "g1", target: "b" },
    ]);

    expect(offsets.get("e1")).toBe(-10);
    expect(offsets.get("e2")).toBe(10);
  });

  it("espalha conexões que entram no mesmo nó quando há uma única origem", () => {
    const offsets = computeEdgePathOffsets([
      { id: "e1", source: "a", target: "g1" },
      { id: "e2", source: "b", target: "g1" },
      { id: "e3", source: "c", target: "g1" },
    ]);

    expect(offsets.get("e1")).toBe(-20);
    expect(offsets.get("e2")).toBe(0);
    expect(offsets.get("e3")).toBe(20);
  });
});

describe("adjustEdgeLabelPosition", () => {
  it("desloca rótulo que cairia sobre um nó intermediário", () => {
    const adjusted = adjustEdgeLabelPosition(
      { x: 200, y: 120 },
      {
        sourceX: 120,
        sourceY: 120,
        targetX: 280,
        targetY: 120,
        sourceNodeId: "s",
        targetNodeId: "t",
      },
      [
        { id: "s", position: { x: 80, y: 84 }, type: "process" },
        { id: "mid", position: { x: 166, y: 84 }, type: "process" },
        { id: "t", position: { x: 280, y: 84 }, type: "process" },
      ]
    );

    expect(adjusted.y).not.toBe(120);
  });
});
