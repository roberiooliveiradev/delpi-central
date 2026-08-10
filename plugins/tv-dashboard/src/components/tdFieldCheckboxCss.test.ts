import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Regressão: `.td-field input { width: 100% }` esticava checkboxes e cortava rótulos
 * em «Campos de valor» (NativeCheckboxControl dentro de DeckField).
 * Também não pode esticar `.delpi-ui-combobox-number__input` do NumberStepper
 * (casas decimais / tamanho de fonte).
 */
describe("td-field checkbox CSS contract", () => {
  const css = readFileSync(
    resolve(dirname(fileURLToPath(import.meta.url)), "../index.css"),
    "utf8",
  );

  it("exclui checkbox/radio e delpi-ui das regras de width:100% em .td-field", () => {
    expect(css).toContain(
      '.td-field input:not([class*="delpi-ui-"]):not([type="checkbox"]):not([type="radio"]):not([type="file"]):not([type="hidden"])',
    );
    expect(css).toContain(
      '.td-deck-inspector--side .td-field input:not([class*="delpi-ui-"]):not([type="checkbox"]):not([type="radio"]):not([type="file"]):not([type="hidden"])',
    );
    expect(css).not.toMatch(
      /\.dashboard-tv-dashboard \.td-field input,\s*\n\.dashboard-tv-dashboard \.td-field select/,
    );
  });

  it("não força input nativo visível no NativeCheckboxControl da sidebar", () => {
    expect(css).toContain(
      ".td-deck-inspector__checkbox:not(.delpi-ui-native-checkbox) input",
    );
    expect(css).not.toMatch(
      /\.td-deck-inspector__checkbox input,\s*\n\.dashboard-tv-dashboard \.td-field \.td-deck-inspector__checkbox input/,
    );
    expect(css).toContain("max-width: 1rem");
  });

  it("lista de colunas no side panel não usa max-height aninhado", () => {
    expect(css).toContain(
      ".td-deck-side-panel .td-deck-inspector__column-list",
    );
    expect(css).toMatch(
      /\.td-deck-side-panel \.td-deck-inspector__column-list[\s\S]*?max-height:\s*none/,
    );
  });
});
