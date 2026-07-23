import { describe, expect, it } from "vitest";

import {
  buildElbowRoutePoints,
  buildRoutedLinePoints,
  normalizeConnectorRouting,
} from "./comunicadoConnectorRouting";
import { createConnectorBlock, createDrawnLineBlock } from "./index";
import type { ComunicadoBlock } from "./comunicadoTypes";

function rect(id: string, x: number, y: number, w = 10, h = 10): ComunicadoBlock {
  return {
    id,
    type: "shape",
    shape: "rectangle",
    frame: { x, y, w, h },
    style: { zIndex: 1 },
  };
}

describe("comunicadoConnectorRouting", () => {
  it("normalizeConnectorRouting aceita elbow/curve", () => {
    expect(normalizeConnectorRouting("elbow")).toBe("elbow");
    expect(normalizeConnectorRouting("curve")).toBe("curve");
    expect(normalizeConnectorRouting("nope")).toBe("straight");
  });

  it("buildElbowRoutePoints gera cotovelos ortogonais", () => {
    const points = buildElbowRoutePoints({ x: 10, y: 10 }, { x: 80, y: 50 }, "e", "w");
    expect(points.length).toBe(4);
    expect(points[1]?.y).toBe(10);
    expect(points[2]?.y).toBe(50);
    expect(points[1]?.x).toBe(points[2]?.x);
  });

  it("createConnectorBlock com routing elbow persiste vértices intermediários", () => {
    const a = rect("a", 0, 0, 20, 10);
    const b = rect("b", 80, 40, 20, 10);
    const line = createConnectorBlock(a, b, { routing: "elbow" });
    expect(line.connector?.routing).toBe("elbow");
    expect((line.vertices?.length ?? 0) >= 3).toBe(true);
  });

  it("createDrawnLineBlock cria seta com snap de âncoras", () => {
    const a = rect("a", 0, 0, 20, 10);
    const b = rect("b", 80, 40, 20, 10);
    const line = createDrawnLineBlock({
      tool: "line-arrow",
      start: { x: 20, y: 5 },
      end: { x: 80, y: 45 },
      blocks: [a, b],
      fromAttach: { blockId: "a", anchor: "e" },
      toAttach: { blockId: "b", anchor: "w" },
    });
    expect(line.shape).toBe("line-arrow-right");
    expect(line.connector?.fromBlockId).toBe("a");
    expect(line.connector?.toBlockId).toBe("b");
  });

  it("buildRoutedLinePoints curve mantém só endpoints", () => {
    expect(buildRoutedLinePoints({ x: 0, y: 0 }, { x: 10, y: 10 }, "curve")).toEqual([
      { x: 0, y: 0 },
      { x: 10, y: 10 },
    ]);
  });
});
