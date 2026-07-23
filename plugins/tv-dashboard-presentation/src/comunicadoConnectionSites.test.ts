import { describe, expect, it } from "vitest";

import {
  findNearestConnectionSite,
  pickNearestAnchorsBetweenBlocks,
  resolveBlockConnectionSites,
} from "./comunicadoConnectionSites";
import { createShapeBlock } from "./comunicadoHelpers";
import type { ComunicadoBlock } from "./comunicadoTypes";

function rect(id: string, x: number, y: number, w = 20, h = 10): ComunicadoBlock {
  return {
    id,
    type: "shape",
    shape: "rectangle",
    frame: { x, y, w, h },
    style: { zIndex: 1 },
  };
}

describe("comunicadoConnectionSites", () => {
  it("resolveBlockConnectionSites expõe N/S/E/W/centro", () => {
    const sites = resolveBlockConnectionSites(rect("a", 0, 0, 20, 10));
    expect(sites.map((site) => site.id).sort()).toEqual(["center", "e", "n", "s", "w"].sort());
    expect(sites.find((site) => site.id === "e")).toEqual({
      blockId: "a",
      id: "e",
      x: 20,
      y: 5,
    });
  });

  it("ponto só tem site center na posição", () => {
    const point = createShapeBlock("point");
    if (point.type !== "shape") return;
    const sites = resolveBlockConnectionSites(point);
    expect(sites).toHaveLength(1);
    expect(sites[0]?.id).toBe("center");
    expect(sites[0]?.x).toBe(45);
    expect(sites[0]?.y).toBe(45);
  });

  it("linha não aceita sites (não é alvo de conector)", () => {
    const line = createShapeBlock("line");
    expect(resolveBlockConnectionSites(line)).toEqual([]);
  });

  it("findNearestConnectionSite respeita limiar", () => {
    const blocks = [rect("a", 0, 0, 20, 10)];
    expect(findNearestConnectionSite({ x: 20, y: 5 }, blocks)?.id).toBe("e");
    expect(findNearestConnectionSite({ x: 50, y: 50 }, blocks, { maxDistancePct: 2 })).toBeNull();
  });

  it("pickNearestAnchorsBetweenBlocks escolhe faces mais próximas", () => {
    const a = rect("a", 0, 0, 20, 10);
    const b = rect("b", 80, 0, 20, 10);
    expect(pickNearestAnchorsBetweenBlocks(a, b)).toEqual({
      fromAnchor: "e",
      toAnchor: "w",
    });
  });
});
