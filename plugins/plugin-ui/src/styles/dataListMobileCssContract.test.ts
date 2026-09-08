import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));

function readCss(name: string) {
  return readFileSync(join(dir, name), "utf8");
}

describe("lista operacional — responsividade mobile (≤768)", () => {
  it("DataListToolbar mantém ações em faixa horizontal scrollável", () => {
    const css = readCss("data-list-toolbar.css");
    expect(css).toMatch(
      /@media \(max-width:\s*768px\)[\s\S]*\.delpi-ui-data-list-toolbar__actions[\s\S]*flex-wrap:\s*nowrap/,
    );
    expect(css).toMatch(
      /@media \(max-width:\s*768px\)[\s\S]*\.delpi-ui-data-list-toolbar__actions[\s\S]*overflow-x:\s*auto/,
    );
    // Negative: não forçar coluna nas ações (empilhava Excel/Fonte/Colunas).
    expect(css).not.toMatch(
      /@media \(max-width:\s*768px\)[\s\S]*\.delpi-ui-data-list-toolbar__actions[\s\S]*flex-direction:\s*column/,
    );
  });

  it("controle de fonte não estica 100% e esconde rótulo no mobile", () => {
    const css = readCss("table-font-size.css");
    expect(css).toMatch(
      /@media \(max-width:\s*768px\)[\s\S]*\.delpi-ui-table-font-size__label[\s\S]*clip:\s*rect\(0,\s*0,\s*0,\s*0\)/,
    );
    expect(css).not.toMatch(
      /@media \(max-width:\s*768px\)[\s\S]*\.delpi-ui-table-font-size\s*\{[^}]*width:\s*100%/,
    );
  });

  it("table-wrap ganha affordance de scroll horizontal no mobile", () => {
    const css = readCss("data-table.css");
    expect(css).toMatch(
      /@media \(max-width:\s*768px\)[\s\S]*\.delpi-ui-table-wrap[\s\S]*background-attachment:\s*local,\s*local,\s*scroll,\s*scroll,\s*local/,
    );
    expect(css).toMatch(/overflow-x:\s*auto/);
  });

  it("InteractiveDataCard usa label|valor em linha no mobile", () => {
    const css = readCss("interactive-data-card.css");
    expect(css).toMatch(
      /@media \(max-width:\s*768px\)[\s\S]*\.delpi-ui-interactive-data-card__field[\s\S]*flex-direction:\s*row/,
    );
    expect(css).toMatch(
      /@media \(max-width:\s*768px\)[\s\S]*\.delpi-ui-interactive-data-card__field[\s\S]*justify-content:\s*space-between/,
    );
  });
});
