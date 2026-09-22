import { describe, expect, it } from "vitest";

import {
  applyRichTextImageWidth,
  clampRichTextImageWidth,
  resolveRichTextImageNaturalSize,
} from "./richTextImageResize";

describe("richTextImageResize", () => {
  it("limita largura ao teto do container e ao mínimo", () => {
    expect(clampRichTextImageWidth(10)).toBe(48);
    expect(clampRichTextImageWidth(900, { containerWidth: 400 })).toBe(400);
    expect(clampRichTextImageWidth(200, { min: 80, max: 180 })).toBe(180);
  });

  it("aplica width/height HTML preservando proporção", () => {
    const img = document.createElement("img");
    Object.defineProperty(img, "naturalWidth", { value: 800 });
    Object.defineProperty(img, "naturalHeight", { value: 400 });
    const size = applyRichTextImageWidth(img, 200);
    expect(size).toEqual({ width: 200, height: 100 });
    expect(img.getAttribute("width")).toBe("200");
    expect(img.getAttribute("height")).toBe("100");
  });

  it("resolve tamanho natural com fallback", () => {
    const img = document.createElement("img");
    expect(resolveRichTextImageNaturalSize(img).width).toBeGreaterThan(0);
  });
});
