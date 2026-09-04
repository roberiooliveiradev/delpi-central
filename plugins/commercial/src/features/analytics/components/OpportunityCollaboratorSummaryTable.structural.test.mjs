#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));
const table = readFileSync(
  join(here, "OpportunityCollaboratorSummaryTable.tsx"),
  "utf8",
);
const page = readFileSync(join(here, "../AnalyticsOpportunitiesPage.tsx"), "utf8");

describe("OpportunityCollaboratorSummaryTable", () => {
  it("usa toolbar kit, sort client-side e callback de drill", () => {
    assert.match(table, /CommercialDataListToolbar/);
    assert.match(table, /useOpportunitiesTablePreferences/);
    assert.match(table, /sortTableRows/);
    assert.match(table, /onSellerClick/);
    assert.match(table, /OPPORTUNITY_COLLABORATOR_COLUMNS_STORAGE_KEY/);
    assert.match(table, /ANALYTICS_COLLABORATOR_SUMMARY_COLUMN_HELP/);
    assert.match(table, /withColumnHelp/);
  });

  it("lista de OVs usa helps de coluna dedicados", () => {
    const list = readFileSync(join(here, "CommercialProposalsTable.tsx"), "utf8");
    assert.match(list, /ANALYTICS_OPPORTUNITY_LIST_COLUMN_HELP/);
    assert.match(list, /withColumnHelp/);
  });

  it("página liga drill para visão oportunidade + seller", () => {
    assert.match(page, /OpportunityCollaboratorSummaryTable/);
    assert.match(page, /onSellerClick/);
    assert.match(page, /setSellerIds/);
    assert.match(page, /setView\("opportunity"\)/);
  });
});
