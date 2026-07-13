import { createBlock } from "@delpi/tv-dashboard-presentation";
import { describe, expect, it } from "vitest";

import { snapComunicadoFrame, snapToGrid } from "./comunicadoSnap";

describe("comunicadoSnap", () => {
  it("alinha ao grid de 5%", () => {
    expect(snapToGrid(23)).toBe(25);
    expect(snapToGrid(22)).toBe(20);
  });

  it("snap move centraliza no eixo quando perto do centro", () => {
    const block = createBlock("text", "A");
    const frame = { x: 41, y: 10, w: 20, h: 20 };
    const snapped = snapComunicadoFrame(block, frame, "move");
    expect(snapped.x).toBe(40);
  });

  it("aceita passo de grade customizado por eixo", () => {
    const block = createBlock("text", "A");
    const frame = { x: 12, y: 12, w: 20, h: 20 };
    const snapped = snapComunicadoFrame(block, frame, "move", {
      xPercent: 10,
      yPercent: 10,
    });
    expect(snapped.x).toBe(10);
    expect(snapped.y).toBe(10);
  });
});
