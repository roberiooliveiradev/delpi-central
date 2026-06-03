import { describe, expect, it } from "vitest";

import { resolveMenuPositionInContainer } from "./menuPositionUtils";

describe("resolveMenuPositionInContainer", () => {
  it("converte coordenadas da viewport para o container do chat", () => {
    const containerRect = {
      left: 240,
      top: 0,
      right: 1040,
      bottom: 800,
      width: 800,
      height: 800,
    };

    const position = resolveMenuPositionInContainer({
      rect: { left: 300, top: 400, right: 380, bottom: 428, width: 80, height: 28 },
      containerRect,
      itemCount: 3,
    });

    expect(position.left).toBe(60);
    expect(position.top).toBeGreaterThanOrEqual(428 - containerRect.top + 6);
  });
});
