#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");

describe("OV → ADY shortcut", () => {
  it("lista e detalhe usam OpenProposalFromOpportunityButton", () => {
    const table = readFileSync(
      join(root, "features/analytics/components/CommercialProposalsTable.tsx"),
      "utf8",
    );
    const detail = readFileSync(
      join(root, "features/analytics/AnalyticsOpportunityDetailPage.tsx"),
      "utf8",
    );
    const button = readFileSync(
      join(root, "features/analytics/components/OpenProposalFromOpportunityButton.tsx"),
      "utf8",
    );
    assert.match(table, /OpenProposalFromOpportunityButton/);
    assert.match(table, /showOpenProposal/);
    assert.match(detail, /OpenProposalFromOpportunityButton/);
    assert.match(detail, /resolvePagePathBack/);
    assert.match(button, /resolveProposalDocumentForOpportunity/);
    assert.match(button, /navigateProposalDetail/);
  });
});
