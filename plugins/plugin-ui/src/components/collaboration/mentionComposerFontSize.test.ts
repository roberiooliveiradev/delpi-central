import { describe, expect, it } from "vitest";

import {
  clampComposerFontSize,
  COMPOSER_FONT_SIZE_MAX,
  COMPOSER_FONT_SIZE_MIN,
} from "./mentionComposerFontSize";

describe("clampComposerFontSize", () => {
  it("limita a faixa do composer (não a do deck)", () => {
    expect(clampComposerFontSize(10)).toBe(COMPOSER_FONT_SIZE_MIN);
    expect(clampComposerFontSize(72)).toBe(COMPOSER_FONT_SIZE_MAX);
    expect(clampComposerFontSize(18)).toBe(18);
  });
});
