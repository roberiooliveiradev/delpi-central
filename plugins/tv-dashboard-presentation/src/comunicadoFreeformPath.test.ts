import { describe, expect, it } from "vitest";

import { createFreeformPathBlock } from "./comunicadoLineDraw";
import { simplifyPolyline, smoothCurveThroughPoints } from "./comunicadoFreeformPath";

describe("comunicadoFreeformPath", () => {
  it("simplifyPolyline reduz pontos colineares", () => {
    const simplified = simplifyPolyline(
      [
        { x: 0, y: 0 },
        { x: 10, y: 0 },
        { x: 20, y: 0 },
        { x: 20, y: 10 },
      ],
      0.5,
    );
    expect(simplified.length).toBeLessThan(4);
    expect(simplified[0]).toEqual({ x: 0, y: 0 });
    expect(simplified[simplified.length - 1]).toEqual({ x: 20, y: 10 });
  });

  it("smoothCurveThroughPoints gera mais pontos que os âncoras", () => {
    const smooth = smoothCurveThroughPoints([
      { x: 0, y: 0 },
      { x: 50, y: 40 },
      { x: 100, y: 0 },
    ]);
    expect(smooth.length).toBeGreaterThan(3);
  });

  it("createFreeformPathBlock cria polilinha e rabisco", () => {
    const poly = createFreeformPathBlock({
      tool: "polyline",
      vertices: [
        { x: 10, y: 10 },
        { x: 40, y: 30 },
        { x: 70, y: 15 },
      ],
    });
    expect(poly?.shape).toBe("polyline");
    expect((poly?.vertices?.length ?? 0) >= 3).toBe(true);

    const scribble = createFreeformPathBlock({
      tool: "scribble",
      vertices: Array.from({ length: 30 }, (_, i) => ({
        x: i * 2,
        y: 20 + Math.sin(i) * 5,
      })),
    });
    expect(scribble?.shape).toBe("scribble");
    expect((scribble?.vertices?.length ?? 0) >= 2).toBe(true);
  });
});
