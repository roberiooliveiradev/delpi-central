import { describe, expect, it } from "vitest";

import { resolveStageContextMenuAnchorClient } from "./resolveStageContextMenuAnchor";

describe("resolveStageContextMenuAnchorClient", () => {
  const canvasRect = { left: 100, top: 50, width: 200, height: 100 };

  it("usa o centro do canvas sem seleção", () => {
    expect(resolveStageContextMenuAnchorClient({ canvasRect, frames: [] })).toEqual({
      x: 200,
      y: 100,
    });
  });

  it("ancora no canto inferior direito do bbox da seleção", () => {
    expect(
      resolveStageContextMenuAnchorClient({
        canvasRect,
        frames: [
          { x: 10, y: 20, w: 30, h: 40 },
          { x: 20, y: 10, w: 10, h: 10 },
        ],
      }),
    ).toEqual({
      x: 100 + (40 / 100) * 200,
      y: 50 + (60 / 100) * 100,
    });
  });
});
