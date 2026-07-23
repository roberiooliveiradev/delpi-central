import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { externalTextBlockEditorKey } from "./ComunicadoEditorTextBlock";

const base = dirname(fileURLToPath(import.meta.url));

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
    const baseBlock = {
      id: "b1",
      type: "text" as const,
      content: "Olá",
      x: 0,
      y: 0,
      width: 100,
      height: 40,
    };
    const withRuns = {
      ...baseBlock,
      contentRuns: [{ text: "Olá", style: { fontWeight: 700 } }],
    };
    const withHref = { ...baseBlock, href: "https://exemplo.test" };
    const keyBase = externalTextBlockEditorKey(baseBlock, 1);
    expect(externalTextBlockEditorKey(withRuns, 1)).not.toBe(keyBase);
    expect(externalTextBlockEditorKey(withHref, 1)).not.toBe(keyBase);
  });
});

describe("text edit commit cleanup contract", () => {
  it("cleanup de edição não depende da identidade de commitPending (evita React #185)", () => {
    const textSrc = readFileSync(join(base, "ComunicadoEditorTextBlock.tsx"), "utf8");
    const shapeSrc = readFileSync(join(base, "ComunicadoEditorShapeBlock.tsx"), "utf8");
    expect(textSrc).toMatch(/commitPendingRef\.current\(\)/);
    expect(textSrc).not.toMatch(/\}, \[isEditing, commitPending\]\)/);
    expect(shapeSrc).toMatch(/commitPendingRef\.current\(\)/);
    expect(shapeSrc).not.toMatch(/\}, \[isEditing, commitPending\]\)/);
    expect(shapeSrc).not.toMatch(/\}, \[isEditing, commitDraft\]\)/);
  });

  it("duplo clique usa enterTextEdit (não selectBlock cru)", () => {
    const textSrc = readFileSync(join(base, "ComunicadoEditorTextBlock.tsx"), "utf8");
    const shapeSrc = readFileSync(join(base, "ComunicadoEditorShapeBlock.tsx"), "utf8");
    const composerSrc = readFileSync(join(base, "ComunicadoComposer.tsx"), "utf8");
    expect(textSrc).toMatch(/enterTextEdit\(block\.id\)/);
    expect(textSrc).toMatch(/cancelPendingTapDeselect\(\)/);
    expect(textSrc).not.toMatch(/selectBlock\(block\.id\)/);
    expect(shapeSrc).toMatch(/enterTextEdit\(block\.id\)/);
    expect(shapeSrc).toMatch(/cancelPendingTapDeselect\(\)/);
    expect(shapeSrc).not.toMatch(/selectBlock\(block\.id\)/);
    expect(composerSrc).toMatch(/resolveStageDblClickAction/);
    expect(composerSrc).not.toMatch(/isolateGroupedBlockOnDoubleClick/);
  });
});
