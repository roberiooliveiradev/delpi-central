import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  buildDashboardTabSearch,
  DASHBOARD_TAB_EFFICIENCY,
  DASHBOARD_TAB_UNPRODUCTIVE_HOURS,
  parseDashboardTab,
  readDashboardTabFromSearch,
} from "../src/utils/dashboardTab.ts";

describe("dashboardTab", () => {
  it("defaults unknown values to efficiency", () => {
    assert.equal(parseDashboardTab(null), DASHBOARD_TAB_EFFICIENCY);
    assert.equal(parseDashboardTab("foo"), DASHBOARD_TAB_EFFICIENCY);
  });

  it("parses unproductive-hours from search", () => {
    assert.equal(
      readDashboardTabFromSearch("?tab=unproductive-hours"),
      DASHBOARD_TAB_UNPRODUCTIVE_HOURS,
    );
    assert.equal(
      readDashboardTabFromSearch("tab=unproductive-hours&x=1"),
      DASHBOARD_TAB_UNPRODUCTIVE_HOURS,
    );
  });

  it("omits default tab from search and keeps other params", () => {
    assert.equal(buildDashboardTabSearch(DASHBOARD_TAB_EFFICIENCY, "?tab=unproductive-hours&x=1"), "?x=1");
    assert.equal(
      buildDashboardTabSearch(DASHBOARD_TAB_UNPRODUCTIVE_HOURS, "?x=1"),
      "?x=1&tab=unproductive-hours",
    );
  });
});
