#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../../..");
const src = join(root, "src");

describe("deep pages fora da top nav", () => {
  it("shell não tem Gestão nem AnalyticsSubNav", () => {
    const shell = readFileSync(join(src, "app/PluginShell.tsx"), "utf8");
    const nav = readFileSync(join(src, "content/shellNav.ts"), "utf8");
    assert.doesNotMatch(shell, /Gestão|AnalyticsSubNav/);
    assert.doesNotMatch(nav, /"Gestão"|"Propostas"/);
  });

  it("OTD, Opp, Equipe e Propostas usam breadcrumb deep", () => {
    for (const relative of [
      "features/analytics/AnalyticsOtdPage.tsx",
      "features/analytics/AnalyticsOpportunitiesPage.tsx",
      "features/analytics/AnalyticsTeamPage.tsx",
      "features/proposals/ProposalsPage.tsx",
    ]) {
      const source = readFileSync(join(src, relative), "utf8");
      assert.match(source, /AnalyticsDeepPagePath/, relative);
    }
    const chrome = readFileSync(
      join(src, "features/analytics/components/AnalyticsDeepPagePath.tsx"),
      "utf8",
    );
    assert.match(chrome, /navigatePluginView\(backView/);
    assert.match(chrome, /backTo/);
    assert.match(chrome, /"overview"/);
  });
});
