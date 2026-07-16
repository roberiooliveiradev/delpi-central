import { describe, expect, it } from "vitest";

import { clampRichTextFontSize } from "./richTextConfig";

describe("richTextConfig", () => {
  it("limita tamanho de fonte", () => {
    expect(clampRichTextFontSize(8)).toBe(10);
    expect(clampRichTextFontSize(80)).toBe(72);
    expect(clampRichTextFontSize(16.4)).toBe(16);
  });
});
