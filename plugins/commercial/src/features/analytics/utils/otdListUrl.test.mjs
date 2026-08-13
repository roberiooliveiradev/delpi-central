#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

import { parseOtdListUrlState } from "./otdListUrl.ts";

const src = join(dirname(fileURLToPath(import.meta.url)), "../../..");

describe("otdListUrl", () => {
  it("parseia busca status sort e página", () => {
    const state = parseOtdListUrlState(
      "?otd_q=WEG&otd_status=late&otd_sort=days_diff&otd_dir=desc&otd_page=3",
    );
    assert.equal(state.search, "WEG");
    assert.equal(state.status, "late");
    assert.equal(state.sortBy, "days_diff");
    assert.equal(state.sortDir, "desc");
    assert.equal(state.page, 3);
  });

  it("ignora status e sort inválidos", () => {
    const state = parseOtdListUrlState("?otd_status=foo&otd_sort=hack");
    assert.equal(state.status, "");
    assert.equal(state.sortBy, null);
  });
});

describe("AnalyticsOtdPage estrutural", () => {
  it("usa lista server-side com busca status sort e paginação", () => {
    const page = readFileSync(
      join(src, "features/analytics/AnalyticsOtdPage.tsx"),
      "utf8",
    );
    assert.match(page, /parseOtdListUrlState/);
    assert.match(page, /writeOtdListUrlState/);
    assert.match(page, /onSortChange/);
    assert.match(page, /CommercialPagination/);
    assert.match(page, /otdLinesSearch/);
    assert.match(page, /sort_by: listState\.sortBy/);
    assert.match(page, /daysDiff/);
    assert.match(page, /insightsRecurrence/);
    assert.match(page, /avg_late_days/);
    assert.match(page, /worstDelays/);
    assert.match(page, /CommercialSpeedometerGauge/);
    assert.match(page, /CommercialHorizontalValueBars/);
    assert.match(page, /latestSeriesPoint/);
  });
});
