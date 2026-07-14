import { describe, expect, it } from "vitest";

import { resolveVisualBoxElementCapabilities } from "./visualBoxElementCapabilities";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

describe("resolveVisualBoxElementCapabilities", () => {
  it("texto: tipografia completa sem galeria de forma", () => {
    const caps = resolveVisualBoxElementCapabilities({
      id: "t1",
      type: "text",
      content: "x",
      frame: { x: 0, y: 0, w: 10, h: 10 },
    } as ComunicadoBlock);
    expect(caps).toMatchObject({
      textHighlight: true,
      paragraphJustify: true,
      paragraphLists: true,
      paragraphNamedStyle: true,
      paragraphSpacing: true,
      shapeGallery: false,
      shapeChrome: true,
      shapeAdjustments: false,
      shapeMarker: false,
    });
  });

  it("forma: mesma tipografia base + Alterar forma; sem listas/estilo nomeado", () => {
    const caps = resolveVisualBoxElementCapabilities({
      id: "s1",
      type: "shape",
      shape: "rectangle",
      frame: { x: 0, y: 0, w: 10, h: 10 },
    } as ComunicadoBlock);
    expect(caps).toMatchObject({
      textHighlight: true,
      clearFormatting: true,
      paragraphJustify: true,
      paragraphLists: false,
      paragraphNamedStyle: false,
      paragraphSpacing: true,
      shapeGallery: true,
      shapeChrome: true,
    });
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
