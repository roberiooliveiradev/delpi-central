import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Painel lateral (placement side / layout pane): seções novas DEVEM usar
 * `DeckPropertySection` com `pane` → FormatPaneSection (borda/accordion).
 *
 * Anti-padrão: `compact={pane}` — vira `td-deck-inspector__section--compact`
 * (só título com pontilhado), regressão visual vs. «Elementos» / «Preparar dados».
 *
 * Canônico: `SelectionPaneSection` ou `<DeckPropertySection pane={pane} …>`.
 */
const PANE_SECTION_SOURCES = [
  "../components/DataSourceLinkSection.tsx",
  "../components/TextDataBindingInspector.tsx",
  "../components/FieldLabelsEditor.tsx",
  "../components/DataPreparePanel.tsx",
  "../components/DataBindingInspector.tsx",
  "../components/VisualDataViewInspector.tsx",
];

describe("DeckPropertySection pane contract", () => {
  it("inspetores de dados no painel usam pane, não compact={pane}", () => {
    const base = dirname(fileURLToPath(import.meta.url));
    for (const relative of PANE_SECTION_SOURCES) {
      const source = readFileSync(join(base, relative), "utf8");
      expect(source, relative).not.toMatch(/compact=\{pane\}/);
      expect(source, relative).toMatch(/pane=\{pane\}|pane\b/);
    }
  });
});
