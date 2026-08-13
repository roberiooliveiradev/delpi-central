#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../../..");
const src = join(root, "src");

describe("Proposals list DataTable pattern (E5.S1)", () => {
  it("página usa wrappers Commercial* e tabela dedicada", () => {
    const page = readFileSync(join(src, "features/proposals/ProposalsPage.tsx"), "utf8");
    assert.match(page, /CommercialPageHero/);
    assert.match(page, /CommercialSectionCard/);
    assert.match(page, /CommercialEmptyState/);
    assert.match(page, /CommercialPagination/);
    assert.match(page, /CommercialTextField/);
    assert.match(page, /ProposalsDocumentsTable/);
    assert.doesNotMatch(page, /from "@delpi\/plugin-ui\/index"/);
    assert.doesNotMatch(page, /\bEmptyState\b/);
    assert.doesNotMatch(page, /\bSectionCard\b/);
  });

  it("tabela tem toolbar Tabela|Cards e cards interativos", () => {
    const table = readFileSync(
      join(src, "features/proposals/ProposalsDocumentsTable.tsx"),
      "utf8",
    );
    assert.match(table, /CommercialDataListToolbar/);
    assert.match(table, /CommercialSegmentToggle/);
    assert.match(table, /CommercialDataTable/);
    assert.match(table, /CommercialInteractiveDataCard/);
    assert.match(table, /CommercialDataCardsGrid/);
    assert.match(table, /CommercialTableFontSizeControls/);
    assert.match(table, /usePersistedViewLayout/);
    assert.match(table, /navigateProposalDetail/);
  });
});
