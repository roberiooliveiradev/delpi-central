#!/usr/bin/env node
/**
 * Gate: KPI ROL do financeiro usa buildKpiGoalPresentation* (meta SI consolidada).
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));

describe("dashboard-financial — meta SI no ROL", () => {
  it("home e RolPage usam buildKpiGoalPresentation*", () => {
    const home = readFileSync(
      join(here, "../pages/DashboardFinancialPage.tsx"),
      "utf8",
    );
    const rolPage = readFileSync(join(here, "../pages/RolPage.tsx"), "utf8");
    const types = readFileSync(join(here, "../types/financial.ts"), "utf8");
    const ids = readFileSync(
      join(here, "../constants/siIndicatorIds.ts"),
      "utf8",
    );

    assert.match(types, /export type RolData = DashboardGoalFields/);
    assert.match(ids, /rol:\s*"commercial-rol"/);
    assert.match(home, /buildKpiGoalPresentationWithBranchIdd/);
    assert.match(home, /FINANCIAL_SI_INDICATORS\.rol/);
    assert.match(home, /realizedValue:\s*rol\?\.rol/);
    assert.match(rolPage, /buildKpiGoalPresentation/);
    assert.match(rolPage, /realizedValue:\s*data\?\.rol/);
  });
});
