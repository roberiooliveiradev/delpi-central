import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * Formatação de trecho (Google Slides TextRun / Canva RichtextRange):
 * ribbon Fonte/Cor/Realce → applyEditingTextRunStylePatch quando há seleção parcial.
 */
describe("partial text format (ribbon → contentRuns)", () => {
  const typography = readFileSync(
    resolve(__dirname, "./FormatRibbonTypographySections.tsx"),
    "utf8",
  );
  const textBlock = readFileSync(
    resolve(__dirname, "../ComunicadoEditorTextBlock.tsx"),
    "utf8",
  );
  const shapeBlock = readFileSync(
    resolve(__dirname, "../ComunicadoEditorShapeBlock.tsx"),
    "utf8",
  );

  it("ribbon encaminha fonte/tamanho/cor/realce ao patch de trecho", () => {
    expect(typography).toContain("applyEditingTextRunStylePatch");
    expect(typography).toContain("applyTextFormatStyle");
    expect(typography).toContain("partialTextSelectionActive");
    expect(typography).toMatch(/applyTextFormatStyle\(\{\s*fontFamily/);
    expect(typography).toMatch(/applyTextFormatStyle\(\{\s*fontSize/);
    expect(typography).toMatch(/applyTextFormatStyle\(\{\s*color/);
    expect(typography).toMatch(/applyTextFormatStyle\(\{\s*textHighlight/);
  });

  it("texto e forma registram applyPartialStylePatch no bridge", () => {
    expect(textBlock).toContain("applyPartialStylePatch");
    expect(textBlock).toContain("useVisualBoxTextEditorBridge");
    expect(shapeBlock).toContain("applyPartialStylePatch");
    expect(shapeBlock).toContain("useVisualBoxTextEditorBridge");
    expect(shapeBlock).toContain("contentRunsFromEditableRoot");
  });

  it("limpar formatação usa clearVisualBoxTextFormatting (zera runs)", () => {
    expect(typography).toContain("clearVisualBoxTextFormatting");
  });

  it("seleção parcial usa lastPartial quando o Range do DOM some no clique", () => {
    expect(typography).toContain("lastPartialTextEditSelection");
    expect(typography).toContain("effectivePartialSelection");
  });

  it("ribbon tenta bridge (Range vivo) antes de tipografia do bloco inteiro", () => {
    expect(typography).toContain("applyToggleOrContainer");
    expect(typography).toContain("fullContentSelectionActive");
    expect(typography).toContain("isFullContentTextSelection");
    expect(typography).toContain("applyEditingTextRunStylePatch(runPatch)");
  });
});
