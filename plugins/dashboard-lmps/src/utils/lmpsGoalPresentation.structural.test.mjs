#!/usr/bin/env node
/**
 * Gate: LMPS usa buildKpiGoalPresentation (não formatGoalSubtitle) no KPI de meta.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));

describe("dashboard-lmps — meta SI presentation", () => {
  it("página usa buildKpiGoalPresentation e não formatGoalSubtitle", () => {
    const page = readFileSync(
      join(here, "../pages/DashboardLmpsPage.tsx"),
      "utf8",
    );
    assert.match(page, /buildKpiGoalPresentation/);
    assert.match(page, /realizedValue:\s*displaySummary\?\.percent_dentro_prazo/);
    assert.doesNotMatch(page, /formatGoalSubtitle/);
  });

  it("recompute de summary preserva DashboardGoalFields", () => {
    const source = readFileSync(join(here, "lmpsClientFilters.ts"), "utf8");
    assert.match(source, /pickDashboardGoalFields/);
    assert.match(source, /goal_scope_hint/);
    assert.match(source, /goal_period_kind/);
    assert.match(source, /\.\.\.pickDashboardGoalFields\(fallback\)/);
  });
});
