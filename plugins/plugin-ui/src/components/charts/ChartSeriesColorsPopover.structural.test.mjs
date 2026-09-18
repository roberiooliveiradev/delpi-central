#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "ChartSeriesColorsPopover.tsx"), "utf8");
const indexSrc = readFileSync(join(here, "index.ts"), "utf8");

describe("ChartSeriesColorsPopover (fonte)", () => {
  it("reutiliza ColorPickerPopoverTrigger e exporta no barrel", () => {
    assert.match(src, /ColorPickerPopoverTrigger/);
    assert.match(src, /FormSelectControl/);
    assert.match(src, /AnchoredPanelPortal/);
    assert.match(src, /onVisibleChange/);
    assert.match(src, /onTrendChange/);
    assert.match(src, /onIncompleteBucketWeightChange/);
    assert.match(src, /onReset/);
    assert.match(src, /variant="fill"/);
    assert.match(src, /showNoFill=\{false\}/);
    assert.match(src, /delpi-ui-chart-series-colors__readonly/);
    assert.match(src, /delpi-ui-chart-series-colors__block/);
    assert.match(src, /delpi-ui-chart-series-colors__pair/);
    assert.match(src, /SectionHintLabel/);
    assert.match(src, /ChartSeriesConfigHints/);
    assert.doesNotMatch(src, /NativeSelectControl/);
    assert.doesNotMatch(src, /<select/);
    assert.match(indexSrc, /ChartSeriesColorsPopover/);
    assert.match(indexSrc, /applySeriesFillPreferences/);
    assert.match(indexSrc, /applySeriesViewPreferences/);
    assert.match(indexSrc, /buildChartSeriesConfigItems/);
  });
});
