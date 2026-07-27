import { describe, expect, it } from "vitest";

import {
  createShapeBlock,
  parseComunicadoConfig,
  resolveLineEndpoints,
  serializeComunicadoConfig,
} from "@delpi/tv-dashboard-presentation";

describe("pasteboard line vertices", () => {
  it("parse/serialize preserva vértices fora do slide (não achata em 0–100)", () => {
    let line = createShapeBlock("line");
    if (line.type !== "shape") throw new Error("expected shape");
    line = {
      ...line,
      vertices: [
        { x: -12, y: -8 },
        { x: 40, y: -20 },
      ],
      frame: { x: -14, y: -22, w: 56, h: 18 },
    };

    const roundTrip = parseComunicadoConfig(
      serializeComunicadoConfig({ version: 4, blocks: [line] }),
    );
    const parsed = roundTrip.blocks?.find((block) => block.id === line.id);
    expect(parsed?.type).toBe("shape");
    if (parsed?.type !== "shape") return;
    const [a, b] = resolveLineEndpoints(parsed);
    expect(a.x).toBeLessThan(0);
    expect(a.y).toBeLessThan(0);
    expect(b.y).toBeLessThan(0);
    expect(a.y).not.toBe(b.y);
  });
});
