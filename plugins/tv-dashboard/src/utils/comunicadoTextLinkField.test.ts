import { describe, expect, it } from "vitest";

import {
  isLikelyExternalUrl,
  normalizeHrefInput,
  resolveDefaultTextLinkMode,
} from "./comunicadoTextLinkField";

describe("comunicadoTextLinkField", () => {
  it("detecta URLs prováveis", () => {
    expect(isLikelyExternalUrl("https://delpi.com")).toBe(true);
    expect(isLikelyExternalUrl("www.exemplo.com")).toBe(true);
    expect(isLikelyExternalUrl("Comunicado interno")).toBe(false);
  });

  it("normaliza www. para https", () => {
    expect(normalizeHrefInput("www.exemplo.com")).toBe("https://www.exemplo.com");
  });

  it("prioriza modo link quando há href ou conteúdo parece URL", () => {
    expect(resolveDefaultTextLinkMode(true, "Título")).toBe("link");
    expect(resolveDefaultTextLinkMode(false, "https://a.com")).toBe("link");
    expect(resolveDefaultTextLinkMode(false, "Aviso")).toBe("text");
  });
});
