import { describe, expect, it } from "vitest";

import { patchComunicadoFrame } from "@delpi/tv-dashboard-presentation";

describe("patchComunicadoFrame", () => {
  const base = { x: 10, y: 20, w: 30, h: 40 };

  it("ajusta largura e reclampa X para caber no palco", () => {
    expect(patchComunicadoFrame(base, "w", 95)).toEqual({
      x: 5,
      y: 20,
      w: 95,
      h: 40,
    });
  });

  it("ajusta posição X sem ultrapassar o limite direito", () => {
    expect(patchComunicadoFrame(base, "x", 90)).toEqual({
      x: 70,
      y: 20,
      w: 30,
      h: 40,
    });
  });

  it("limita tamanho mínimo", () => {
    expect(patchComunicadoFrame(base, "h", 0).h).toBe(0.5);
  });
});
