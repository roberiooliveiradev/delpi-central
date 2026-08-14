#!/usr/bin/env node
/**
 * Gate: inventário Chart View Shell — todo gráfico (exceto scalar/mini) exporta Excel.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const srcRoot = join(here, "../..");

function read(rel) {
  return readFileSync(join(srcRoot, rel), "utf8");
}

const INVENTORY = [
  "features/analytics/components/AnalyticsRolSeriesChart.tsx",
  "features/analytics/components/AnalyticsClosingRateSeriesChart.tsx",
  "features/customers/components/CustomerBillingSeriesChart.tsx",
  "features/customers/billing/components/CustomerAccountBillingChart.tsx",
  "features/customers/components/CustomerPurchaseEvolutionChart.tsx",
  "features/analytics/components/AnalyticsOtdInsightBarChart.tsx",
  "components/OpenOrdersProductionDetailContent.tsx",
  "features/analytics/components/AnalyticsFunnelChart.tsx",
];

const EXPORT_RE = /runTabularExport|ExcelExportButton|CommercialTabularExportButtons|CommercialExcelExportButton/;

describe("chart Excel coverage (inventário Portal)", () => {
  for (const rel of INVENTORY) {
    it(`${rel} exporta tabular/Excel`, () => {
      const src = read(rel);
      assert.match(src, EXPORT_RE, `${rel} sem export Excel`);
    });
  }
});
