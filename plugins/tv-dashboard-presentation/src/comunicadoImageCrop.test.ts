import { describe, expect, it } from "vitest";

import {
  COMUNICADO_IMAGE_CROP_FULL,
  comunicadoImageCropCssProperties,
  isFullComunicadoImageCrop,
  normalizeComunicadoImageCrop,
} from "./comunicadoImageCrop";
import { parseComunicadoConfig, serializeComunicadoConfig } from "./comunicadoHelpers";

describe("comunicadoImageCrop", () => {
  it("normaliza e descarta recorte total", () => {
    expect(normalizeComunicadoImageCrop(COMUNICADO_IMAGE_CROP_FULL)).toBeUndefined();
    expect(isFullComunicadoImageCrop(undefined)).toBe(true);
  });

  it("limita região dentro da imagem", () => {
    expect(normalizeComunicadoImageCrop({ x: 80, y: 0, w: 50, h: 100 })).toEqual({
      x: 50,
      y: 0,
      w: 50,
      h: 100,
    });
  });

  it("gera estilo CSS para viewport parcial", () => {
    const style = comunicadoImageCropCssProperties({ x: 25, y: 0, w: 50, h: 100 }, "contain");
    expect(style.width).toBe("200%");
    expect(style.height).toBe("100%");
    expect(style.marginLeft).toBe("-50%");
  });

  it("round-trip imageCrop no serialize", () => {
    const parsed = parseComunicadoConfig({
      version: 4,
      blocks: [
        {
          id: "img1",
          type: "image",
          assetId: "a1",
          imageCrop: { x: 10, y: 5, w: 60, h: 80 },
          frame: { x: 0, y: 0, w: 50, h: 50 },
        },
      ],
    });
    expect(parsed.blocks?.[0]?.type).toBe("image");
    if (parsed.blocks?.[0]?.type === "image") {
      expect(parsed.blocks[0].imageCrop).toEqual({ x: 10, y: 5, w: 60, h: 80 });
    }
    const serialized = serializeComunicadoConfig(parsed);
    const blocks = serialized.blocks as Array<Record<string, unknown>>;
    expect(blocks[0].imageCrop).toEqual({ x: 10, y: 5, w: 60, h: 80 });
  });
});
