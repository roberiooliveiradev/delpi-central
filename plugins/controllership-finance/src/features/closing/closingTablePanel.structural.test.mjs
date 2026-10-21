#!/usr/bin/env node
/**
 * Contrato do painel de resultados das tabelas da Central (docs 51/52):
 * banda única header+toolbar via CSS escopado, colunas com classes do kit,
 * sem segunda tabela/toolbar e sem controles inertes. Quebra se alguém
 * remover a composição ou recriar DataTable fora do DataTableSection.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));
const src = join(here, "..", "..");

const css = readFileSync(join(src, "index.css"), "utf8");
const settlements = readFileSync(
  join(here, "FinancialSettlementsPage.tsx"),
  "utf8",
);
const stock = readFileSync(join(here, "StockInventoryPage.tsx"), "utf8");

describe("painel de tabela — composição CSS (doc 52 §2)", () => {
  it("section usa flex-wrap para banda header+toolbar", () => {
    assert.match(css, /\.cf-table-section\s*\{[^}]*display:\s*flex/);
    assert.match(css, /\.cf-table-section\s*\{[^}]*flex-wrap:\s*wrap/);
  });

  it("toolbar alinhada à direita na banda e full-width no mobile", () => {
    assert.match(css, /\.cf-table-toolbar\s*\{[^}]*flex:\s*0 0 auto/);
    assert.match(css, /max-width:\s*768px[^}]*\.cf-table-toolbar/s);
  });

  it("contagem em pill (meta) e densidade via token do kit", () => {
    assert.match(css, /\.cf-table-section__meta\s*\{[^}]*border-radius/);
    assert.match(css, /--delpi-ui-table-cell-pad-y/);
  });
});

describe("painel de tabela — uso do kit nas páginas", () => {
  for (const [name, code] of [
    ["FinancialSettlementsPage", settlements],
    ["StockInventoryPage", stock],
  ]) {
    it(`${name}: DataTableSection único com prefs e paginação server`, () => {
      assert.match(code, /DataTableSection</);
      assert.match(code, /columnPreferencesKey=/);
      assert.match(code, /fontSizePreferencesKey=/);
      assert.match(code, /serverPagination=/);
      assert.match(code, /resizableColumns/);
      assert.match(code, /hideSearch/);
      // sem fork do kit nem toolbar paralela
      assert.doesNotMatch(code, /from\s+"@delpi\/plugin-ui\/index"[^;]*\bDataTable\b/);
      assert.doesNotMatch(code, /toolbarLeading=|toolbarExtra=/);
      // sem controles visuais inertes (Excel/Cards/Board fora de contrato)
      assert.doesNotMatch(code, /excelExport=|renderCard=|viewLayoutPreferencesKey=/);
    });

    it(`${name}: colunas usam classes de proporção do kit`, () => {
      assert.match(code, /cf-table__col--(compact|wrap|wide|status|numeric)/);
    });
  }

  it("R03 não renderiza tabela quando o snapshot está ausente (T18)", () => {
    assert.match(stock, /payload\?\.status\s*!==\s*"source_missing"/);
  });
});
