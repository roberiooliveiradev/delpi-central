#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));

describe("OverviewPage — paridade dashboard", () => {
  it("hero IDD + KPIs Meta/Nota IDD sem api-delpi (incl. carteira aberta)", () => {
    const source = readFileSync(join(here, "OverviewPage.tsx"), "utf8");
    assert.match(source, /DepartmentIddBadge/);
    assert.match(source, /CommercialDashboardKpiCard/);
    assert.match(source, /buildRolPerUnitKpiView/);
    assert.match(source, /buildKpiGoalPresentationWithBranchIdd/);
    assert.match(source, /open_portfolio|openPortfolio/);
    assert.doesNotMatch(source, /apiDelpiUrl|\/apps\/api-delpi/);
    const kpiCount = (source.match(/<CommercialDashboardKpiCard/g) ?? []).length;
    assert.equal(kpiCount, 7);
  });
});
