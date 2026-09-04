#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));

describe("dashboard-commercial — meta consolidada SI", () => {
  it("rolPerUnitPresentation não inventa hint local no consolidado", () => {
    const source = readFileSync(join(here, "rolPerUnitPresentation.ts"), "utf8");
    assert.match(source, /consolidatedMetric/);
    assert.match(source, /buildKpiGoalPresentation/);
    assert.doesNotMatch(source, /BRANCH_GOALS_FILTER_HINT/);
    assert.doesNotMatch(source, /Selecione uma unidade no filtro/);
  });

  it("página e hook passam payload consolidado SI", () => {
    const page = readFileSync(
      join(here, "../pages/DashboardCommercialPage.tsx"),
      "utf8",
    );
    const hook = readFileSync(
      join(here, "../hooks/useCommercialDashboard.ts"),
      "utf8",
    );
    assert.match(page, /consolidatedMetric:\s*consolidatedRol/);
    assert.match(page, /consolidatedMetric:\s*consolidatedWegRol/);
    assert.match(page, /consolidatedMetric:\s*consolidatedNewBusinessRol/);
    assert.match(hook, /getRolSummary\(rolMetricParams,/);
    assert.match(hook, /setConsolidatedRol/);
    assert.match(hook, /setConsolidatedWegRol/);
    assert.match(hook, /setConsolidatedNewBusinessRol/);
  });
});
