import { describe, expect, it } from "vitest";

import {
  buildFindSnippet,
  splitFindHighlightSegments,
} from "./roomMessageFindHighlight";

describe("roomMessageFindHighlight", () => {
  it("parte segmentos com match case-insensitive", () => {
    expect(splitFindHighlightSegments("abc Teste xyz", "teste")).toEqual([
      { text: "abc ", match: false },
      { text: "Teste", match: true },
      { text: " xyz", match: false },
    ]);
  });

  it("monta snippet com reticências em torno do termo", () => {
    const long = `${"x".repeat(80)}alvo${"y".repeat(80)}`;
    const snippet = buildFindSnippet(long, "alvo", 10);
    expect(snippet).toMatch(/…/);
    expect(snippet).toMatch(/alvo/);
  });
});
