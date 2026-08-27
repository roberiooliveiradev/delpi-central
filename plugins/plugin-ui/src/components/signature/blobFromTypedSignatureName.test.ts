import { describe, expect, it, vi } from "vitest";

import {
  fitTypedSignatureFontSize,
  TYPED_SIGNATURE_FONT_FAMILY,
} from "./blobFromTypedSignatureName";

describe("fitTypedSignatureFontSize", () => {
  it("reduz font-size quando o nome script excede a largura útil", () => {
    const measureText = vi.fn((text: string) => ({
      width: text.length * 18,
      actualBoundingBoxAscent: 40,
      actualBoundingBoxDescent: 12,
    }));
    const ctx = {
      font: "",
      measureText,
    } as unknown as CanvasRenderingContext2D;

    const fontSize = fitTypedSignatureFontSize(
      ctx,
      "Evelyn Eduarda da Silva",
      280,
      160,
      22,
      56,
    );

    expect(fontSize).toBeLessThanOrEqual(56);
    expect(fontSize).toBeGreaterThanOrEqual(22);
    expect(measureText).toHaveBeenCalled();
    expect(ctx.font).toContain(TYPED_SIGNATURE_FONT_FAMILY);
  });

  it("usa o máximo quando o nome curto cabe no canvas", () => {
    const measureText = vi.fn((text: string) => ({
      width: text.length * 8,
      actualBoundingBoxAscent: 30,
      actualBoundingBoxDescent: 8,
    }));
    const ctx = {
      font: "",
      measureText,
    } as unknown as CanvasRenderingContext2D;

    const fontSize = fitTypedSignatureFontSize(ctx, "Ana", 520, 160, 22, 56);
    expect(fontSize).toBe(56);
  });
});
