#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "MultiTypeSeriesChart.tsx"), "utf8");

describe("MultiTypeSeriesChart (fonte)", () => {
  it("suporta column line area pie e tendência", () => {
    assert.match(src, /chartType === "pie"/);
    assert.match(src, /chartType === "line"/);
    assert.match(src, /chartType === "area"/);
    assert.match(src, /horizontal_bar/);
    assert.match(src, /withLinearTrendField/);
    assert.match(src, /ComposedChart/);
    assert.match(src, /TREND_STROKE_WIDTH/);
    assert.match(src, /trendSources\.length > 1/);
    assert.match(src, /yAxisId=\{seriesAxisId\(source/);
    assert.doesNotMatch(src, /delpi-ui-chart-trend-stroke/);
  });

  it("aplica fill por categoria quando categoryFillKey está definido", () => {
    assert.match(src, /categoryFillKey\?:/);
    assert.match(src, /resolveCategoryFill/);
  });

  it("expõe showValueLabels opt-in com LabelList nas barras", () => {
    assert.match(src, /showValueLabels\?:/);
    assert.match(src, /LabelList/);
    assert.match(src, /barValueLabels/);
  });

  it("aplica showValueLabels nos pontos do gráfico de linha", () => {
    assert.match(src, /chartType === "line"/);
    assert.match(src, /pointLabels\(showValueLabels\)/);
  });

  it("remonta o plot quando a ordem das séries muda (Recharts 3 bar store)", () => {
    assert.match(src, /seriesOrderKey/);
    assert.match(src, /key=\{seriesOrderKey\}/);
    assert.match(src, /itemSorter=\{null\}/);
  });

  it("expõe eixo Y secundário e linha para séries overlay", () => {
    assert.match(src, /formatYSecondary\?:/);
    assert.match(src, /secondaryDataKeys\?:/);
    assert.match(src, /axis\?: "primary" \| "secondary"/);
    assert.match(src, /plotAs\?: "bar" \| "line"/);
    assert.match(src, /yAxisId="right"/);
    assert.match(src, /delpi-ui-multi-type-series-chart--dual-y/);
    assert.match(src, /overflow: "visible"/);
  });
});
