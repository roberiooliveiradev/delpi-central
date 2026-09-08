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
    assert.match(src, /AnchoredPanelPortal/);
    assert.match(src, /onReset/);
    assert.match(src, /variant="fill"/);
    assert.match(src, /showNoFill=\{false\}/);
    assert.match(indexSrc, /ChartSeriesColorsPopover/);
    assert.match(indexSrc, /applySeriesFillPreferences/);
  });
});
