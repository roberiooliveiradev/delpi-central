import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/** Voltar à home fica na top bar, antes de Desfazer/Refazer. */
describe("deck history back button contract", () => {
  const base = dirname(fileURLToPath(import.meta.url));
  const history = readFileSync(join(base, "DeckHistoryTabActions.tsx"), "utf8");
  const chrome = readFileSync(join(base, "../DeckEditorChrome.tsx"), "utf8");

  it("renderiza Voltar antes dos botões de histórico", () => {
    const backIdx = history.indexOf("ArrowLeft");
    const undoIdx = history.indexOf("Undo2");
    expect(backIdx).toBeGreaterThan(-1);
    expect(undoIdx).toBeGreaterThan(-1);
    expect(backIdx).toBeLessThan(undoIdx);
    expect(history).toMatch(/onBack\?:/);
    expect(history).toMatch(/Voltar à lista de programações/);
  });

  it("chrome passa onBack da programação para o histórico", () => {
    expect(chrome).toMatch(/DeckHistoryTabActions onBack=\{playlistChrome\?\.onBack\}/);
  });
});
