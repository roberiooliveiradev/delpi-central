#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

import { ANALYTICS_CONTENT } from "../../../content/analyticsContent.ts";
import { OVERVIEW_METRIC_BY_ID } from "../../../content/overviewMetricsCatalog.ts";

const here = dirname(fileURLToPath(import.meta.url));

describe("analytics unit labels (content + helper)", () => {
  it("content analytics/overview usam Unidade e estados", () => {
    assert.equal(ANALYTICS_CONTENT.filters.branch, "Unidade (indicadores)");
    assert.equal(OVERVIEW_METRIC_BY_ID.rol_branch.label, "ROL por unidade");
    assert.match(OVERVIEW_METRIC_BY_ID.rol_series.tooltip, /Santa Catarina/);
    assert.match(OVERVIEW_METRIC_BY_ID.rol_series.tooltip, /Espírito Santo/);
    assert.doesNotMatch(ANALYTICS_CONTENT.filters.branch, /^Filial$/);
  });

  it("helper deriva séries ROL/OTD do kit operationalUnitLabels", () => {
    const source = readFileSync(join(here, "analyticsBranchFilters.ts"), "utf8");
    assert.match(source, /formatOperationalUnitCode/);
    assert.match(source, /ANALYTICS_UNIT_FIELD_LABEL = "Unidade \(indicadores\)"/);
    assert.match(source, /ANALYTICS_ROL_SERIES_LABELS/);
    assert.match(source, /ANALYTICS_OTD_SERIES_LABELS/);
    assert.match(source, /OPERATIONAL_UNIT_OPTIONS/);
  });
});
