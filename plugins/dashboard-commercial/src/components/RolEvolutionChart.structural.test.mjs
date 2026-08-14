#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

describe("RolEvolutionChart (fonte)", () => {
  it("usa colunas agrupadas locais sem importar commercial", () => {
    const chart = readFileSync(join(here, "RolEvolutionChart.tsx"), "utf8");
    assert.match(chart, /GroupedColumnSeriesChart/);
    assert.match(chart, /showTrend/);
    assert.match(chart, /NativeCheckboxControl/);
    assert.doesNotMatch(chart, /LineChart/);
    assert.doesNotMatch(chart, /plugins\/commercial|@delpi\/commercial/);
  });
});
