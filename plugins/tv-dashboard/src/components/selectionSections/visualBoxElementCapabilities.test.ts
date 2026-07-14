import { describe, expect, it } from "vitest";

import { resolveVisualBoxElementCapabilities } from "./visualBoxElementCapabilities";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

describe("resolveVisualBoxElementCapabilities", () => {
  it("texto e forma compartilham tipografia + Alterar forma + chrome", () => {
    const textCaps = resolveVisualBoxElementCapabilities({
      id: "t1",
      type: "text",
      content: "x",
      frame: { x: 0, y: 0, w: 10, h: 10 },
    } as ComunicadoBlock);
    const shapeCaps = resolveVisualBoxElementCapabilities({
      id: "s1",
      type: "shape",
      shape: "rectangle",
      frame: { x: 0, y: 0, w: 10, h: 10 },
    } as ComunicadoBlock);

    for (const caps of [textCaps, shapeCaps]) {
      expect(caps).toMatchObject({
        textHighlight: true,
        clearFormatting: true,
        paragraphJustify: true,
        paragraphLists: true,
        paragraphNamedStyle: true,
        paragraphSpacing: true,
        shapeGallery: true,
        shapeChrome: true,
      });
    }
  });

  it("marcador só em ponto", () => {
    const point = resolveVisualBoxElementCapabilities({
      id: "p1",
      type: "shape",
      shape: "point",
      frame: { x: 0, y: 0, w: 5, h: 5 },
    } as ComunicadoBlock);
    expect(point?.shapeMarker).toBe(true);
    expect(point?.shapeChrome).toBe(true);
  });

  it("retorna null fora da caixa visual", () => {
    expect(
      resolveVisualBoxElementCapabilities({
        id: "i1",
        type: "icon",
        iconName: "Package",
        frame: { x: 0, y: 0, w: 10, h: 10 },
      } as ComunicadoBlock),
    ).toBeNull();
  });
});
