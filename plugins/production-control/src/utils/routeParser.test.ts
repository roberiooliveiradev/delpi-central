import { describe, expect, it } from "vitest";

import { buildPpcHref, parsePpcPath } from "./routeParser";

describe("parsePpcPath", () => {
  it("defaults empty base path to home", () => {
    const route = parsePpcPath("/apps/production-control", "", "01");
    expect(route.subpluginId).toBe("home");
    expect(route.branch).toBe("01");
    expect(route.detectorId).toBeNull();
  });

  it("reads detector and branch from query", () => {
    const route = parsePpcPath(
      "/apps/production-control/problem-analysis",
      "?branch=02&detector=incomplete-order-sets",
      "01",
    );
    expect(route.subpluginId).toBe("problem-analysis");
    expect(route.branch).toBe("02");
    expect(route.detectorId).toBe("incomplete-order-sets");
  });

  it("reads work center, period and locate query from the deep link", () => {
    const route = parsePpcPath(
      "/apps/production-control/machine-load",
      "?branch=01&ct=CT-02&startDate=2026-08-24&endDate=2026-08-28&locate=90262910",
      "02",
    );
    expect(route.subpluginId).toBe("machine-load");
    expect(route.workCenter).toBe("CT-02");
    expect(route.startDate).toBe("2026-08-24");
    expect(route.endDate).toBe("2026-08-28");
    expect(route.locateQuery).toBe("90262910");
  });

  it("ignores malformed dates instead of forwarding them to the API", () => {
    const route = parsePpcPath(
      "/apps/production-control/machine-load",
      "?branch=01&startDate=24%2F08%2F2026&endDate=",
      "01",
    );
    expect(route.startDate).toBeNull();
    expect(route.endDate).toBeNull();
  });
});

describe("buildPpcHref", () => {
  it("keeps home on the plugin base path", () => {
    expect(buildPpcHref({ subpluginId: "home", branch: "01" })).toBe(
      "/apps/production-control?branch=01",
    );
  });

  it("serializes the detector deep link", () => {
    expect(
      buildPpcHref({
        subpluginId: "problem-analysis",
        branch: "01",
        detectorId: "incomplete-order-sets",
      }),
    ).toBe("/apps/production-control/problem-analysis?branch=01&detector=incomplete-order-sets");
  });

  it("keeps the work center tab, period and locate query in the deep link", () => {
    expect(
      buildPpcHref({
        subpluginId: "machine-load",
        branch: "02",
        workCenter: "CT-02",
        startDate: "2026-08-24",
        endDate: "2026-08-28",
        locateQuery: "90262910",
      }),
    ).toBe(
      "/apps/production-control/machine-load?branch=02&ct=CT-02&startDate=2026-08-24&endDate=2026-08-28&locate=90262910",
    );
  });
});
