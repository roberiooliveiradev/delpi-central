import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)));

describe("AnalyticsClosingRateSeriesChart", () => {
  it("usa BFF série, export e labels SC/ES", () => {
    const chart = readFileSync(join(root, "AnalyticsClosingRateSeriesChart.tsx"), "utf8");
    assert.match(chart, /getSalesConversionRateSeries/);
    assert.match(chart, /buildOverviewClosingRateSeriesPayload/);
    assert.match(chart, /ANALYTICS_CONVERSION_SERIES_LABELS/);
    assert.match(chart, /CM_HELP\.overview\.closingRateSeries/);
    assert.match(chart, /CommercialChartToolbar/);
    assert.match(chart, /comparePriorYear|NativeCheckboxControl/);
    assert.match(chart, /shiftPeriodRangeByYears|mergeSeriesWithPriorYear/);
    assert.match(chart, /closingRateSeriesYoy/);
  });
});
