import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Regressão: `.td-field input { width: 100% }` esticava checkboxes e cortava rótulos
 * em «Campos de valor» (NativeCheckboxControl dentro de DeckField).
 */
describe("td-field checkbox CSS contract", () => {
  const css = readFileSync(
    resolve(dirname(fileURLToPath(import.meta.url)), "../index.css"),
    "utf8",
  );

  it("exclui checkbox/radio das regras de width:100% em .td-field", () => {
    expect(css).toMatch(
      /\.td-field input:not\(\[type="checkbox"\]\):not\(\[type="radio"\]\)/,
    );
    expect(css).not.toMatch(
      /\.dashboard-tv-dashboard \.td-field input,\s*\n\.dashboard-tv-dashboard \.td-field select/,
    );
  });

  it("fixa tamanho do input do checkbox no inspector", () => {
    expect(css).toMatch(
      /\.td-field \.delpi-ui-native-checkbox input[\s\S]*?max-width:\s*1rem/,
    );
  });
});
