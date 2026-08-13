#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  OVERVIEW_METRICS,
  OVERVIEW_METRIC_BY_ID,
  overviewMetricTooltip,
} from "./overviewMetricsCatalog.ts";

const REQUIRED_IDS = [
  "rol",
  "rol_weg",
  "rol_new_business",
  "closing_rate",
  "open_portfolio",
  "otd",
  "new_business_pct",
  "rol_series",
  "closing_rate_series",
  "funnel",
];

describe("overviewMetricsCatalog", () => {
  it("expõe todas as métricas da Visão geral com tooltip", () => {
    assert.equal(OVERVIEW_METRICS.length, REQUIRED_IDS.length);
    for (const id of REQUIRED_IDS) {
      const metric = OVERVIEW_METRIC_BY_ID[id];
      assert.ok(metric, id);
      assert.ok(metric.label.trim(), id);
      assert.ok(metric.tooltip.trim(), id);
      assert.equal(overviewMetricTooltip(id), metric.tooltip);
    }
  });
});
