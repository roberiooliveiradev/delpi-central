import { describe, expect, it } from "vitest";

import { externalTextBlockEditorKey } from "./ComunicadoEditorTextBlock";

describe("externalTextBlockEditorKey", () => {
  it("ignora mudança só de referência quando conteúdo é igual", () => {
    const a = {
      id: "b1",
      type: "text" as const,
      content: "Olá",
      x: 0,
      y: 0,
      width: 100,
      height: 40,
    };
    const b = { ...a, style: { fontSize: 14 } };
    expect(externalTextBlockEditorKey(a, 1)).toBe(externalTextBlockEditorKey(b, 1));
  });

  it("muda quando contentRuns ou href mudam", () => {
    const base = {
      id: "b1",
      type: "text" as const,
      content: "Olá",
      x: 0,
      y: 0,
      width: 100,
      height: 40,
    };
    const withRuns = {
      ...base,
      contentRuns: [{ text: "Olá", style: { fontWeight: 700 } }],
    };
    const withHref = { ...base, href: "https://exemplo.test" };
    const keyBase = externalTextBlockEditorKey(base, 1);
    expect(externalTextBlockEditorKey(withRuns, 1)).not.toBe(keyBase);
    expect(externalTextBlockEditorKey(withHref, 1)).not.toBe(keyBase);
  });
});
