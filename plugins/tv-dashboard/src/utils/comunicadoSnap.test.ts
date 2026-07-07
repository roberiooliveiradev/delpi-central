import { describe, expect, it } from "vitest";

import { snapComunicadoFrame, snapToGrid } from "./comunicadoSnap";

describe("comunicadoSnap", () => {
  it("alinha ao grid de 5%", () => {
    expect(snapToGrid(23)).toBe(25);
    expect(snapToGrid(22)).toBe(20);
  });

  it("snap move centraliza no eixo quando perto do centro", () => {
    const frame = { x: 49, y: 10, w: 20, h: 20 };
    const snapped = snapComunicadoFrame(frame, "move");
    expect(snapped.x).toBe(40);
  });
});
