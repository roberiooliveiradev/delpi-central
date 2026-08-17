#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));

describe("AnalyticsRolSeriesChart — paridade dashboard", () => {
  it("usa séries SC/ES, toolbar Dia–Ano e drill", () => {
    const chart = readFileSync(join(here, "AnalyticsRolSeriesChart.tsx"), "utf8");
    assert.match(chart, /CommercialTabularExportButtons/);
    assert.match(chart, /buildOverviewRolSeriesPayload/);
    assert.match(chart, /CommercialChartGranularityToggle/);
    assert.match(chart, /ChartOverlayOptionsPopover/);
    assert.match(chart, /resolveAnalyticsSeriesUnits/);
    assert.match(chart, /filters\.branch/);
    assert.doesNotMatch(chart, /CommercialChartToolbar/);
    assert.doesNotMatch(chart, /NativeCheckboxControl/);
    assert.match(chart, /"year"/);
    assert.match(chart, /onDrillDown/);
    assert.match(chart, /shiftPeriodRangeByYears|mergeSeriesWithPriorYear/);
    assert.match(chart, /ChartViewShell|MultiTypeSeriesChart/);
    assert.match(chart, /usePersistedChartPreferences/);
    assert.doesNotMatch(chart, /LineChart/);
    assert.doesNotMatch(chart, /ROL filial|ROL matriz/);
  });

  it("Overview liga drill e branch aos filtros", () => {
    const overview = readFileSync(
      join(here, "../../overview/OverviewPage.tsx"),
      "utf8",
    );
    assert.match(overview, /onDrillDown/);
    assert.match(overview, /replaceDateFilters/);
    assert.match(overview, /branch:\s*filters\.apiParams\.branch/);
  });
});
