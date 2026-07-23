import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

/**
 * Regressão: clique em Negrito na ribbon não pode cair no estilo do bloco inteiro
 * quando havia seleção parcial («Texto teste |negrito|»).
 */
describe("partial range fallback (ribbon → contentRuns)", () => {
  const bridge = readFileSync(resolve(__dirname, "./useVisualBoxTextEditorBridge.ts"), "utf8");
  const ribbonBtn = readFileSync(resolve(__dirname, "../components/tdRibbonUi.tsx"), "utf8");
  const typography = readFileSync(
    resolve(__dirname, "../components/formatRibbon/FormatRibbonTypographySections.tsx"),
    "utf8",
  );

  it("bridge guarda lastPartialRange e resolvePartialRange", () => {
    expect(bridge).toContain("lastPartialRangeRef");
    expect(bridge).toContain("resolvePartialRange");
    expect(bridge).toMatch(/live\.end > live\.start/);
    expect(bridge).toContain("selectionchange");
    expect(bridge).toContain("selectionSyncEnabled");
  });

  it("botão da ribbon faz preventDefault no mousedown", () => {
    expect(ribbonBtn).toContain("PRESERVE_TEXT_EDIT_FOCUS_ATTR");
    expect(ribbonBtn).toContain("onMouseDown");
    expect(ribbonBtn).toContain("preventDefault");
  });

  it("ribbon usa lastPartialTextEditSelection quando a seleção viva some", () => {
    expect(typography).toContain("lastPartialTextEditSelection");
    expect(typography).toContain("effectivePartialSelection");
    expect(typography).toContain("partialTextSelectionActive");
  });
});
