#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(
  join(__dirname, "GroupedColumnSeriesChart.tsx"),
  "utf8",
);
const content = readFileSync(
  join(__dirname, "../content/customerBillingContent.ts"),
  "utf8",
);

describe("GroupedColumnSeriesChart (fonte)", () => {
  it("usa ComposedChart com Bar agrupadas e Line de tendência", () => {
    assert.match(src, /ComposedChart/);
    assert.match(src, /\bBar\b/);
    assert.match(src, /\bLine\b/);
    assert.match(src, /withLinearTrendField/);
    assert.match(src, /showTrend/);
    assert.match(src, /trendSource/);
    assert.doesNotMatch(src, /AreaChart|\bArea\b/);
  });

  it("expõe copy do toggle de tendência no content", () => {
    assert.match(content, /showTrendLine/);
    assert.match(content, /Linha de tendência/);
  });
});
