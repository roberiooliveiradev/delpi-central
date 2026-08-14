#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

import {
  clampCompareYears,
  compareYearOffsets,
  MAX_COMPARE_YEARS,
} from "../utils/compareYears.ts";

const here = dirname(fileURLToPath(import.meta.url));

describe("PeriodCompareControls helpers", () => {
  it("clampCompareYears limita 0–3 (kit)", () => {
    assert.equal(clampCompareYears(-1), 0);
    assert.equal(clampCompareYears(0), 0);
    assert.equal(clampCompareYears(1), 1);
    assert.equal(clampCompareYears(2), 2);
    assert.equal(clampCompareYears(3), 3);
    assert.equal(clampCompareYears(9), 3);
    assert.equal(MAX_COMPARE_YEARS, 3);
  });

  it("compareYearOffsets gera offsets negativos (kit)", () => {
    assert.deepEqual(compareYearOffsets(0), []);
    assert.deepEqual(compareYearOffsets(1), [-1]);
    assert.deepEqual(compareYearOffsets(2), [-1, -2]);
    assert.deepEqual(compareYearOffsets(3), [-1, -2, -3]);
  });

  it("componente só período — overlays no ChartViewShell", () => {
    const source = readFileSync(join(here, "PeriodCompareControls.tsx"), "utf8");
    assert.match(source, /BILLING_SERIES_PRESET_OPTIONS/);
    assert.doesNotMatch(source, /NativeCheckboxControl|AnchoredPanelPortal/);
    assert.doesNotMatch(source, /apiDelpiUrl|API_DELPI|\/apps\/api-delpi/);
    assert.doesNotMatch(source, /\.delpi-ui-/);
  });
});
