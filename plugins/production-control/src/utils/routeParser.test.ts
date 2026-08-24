import { describe, expect, it } from "vitest";

import { buildPpcHref, parsePpcPath, readMaterialsDetailDeepLink } from "./routeParser";

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

  it("reads the demand search and status from the deep link", () => {
    const route = parsePpcPath(
      "/apps/production-control/demand",
      "?branch=01&q=90262910&status=late",
      "01",
    );
    expect(route.subpluginId).toBe("demand");
    expect(route.demandSearch).toBe("90262910");
    expect(route.demandStatus).toBe("late");
  });

  it("drops a demand status outside the API contract", () => {
    const route = parsePpcPath("/apps/production-control/demand", "?status=urgente", "01");
    expect(route.demandStatus).toBeNull();
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

  it("serializes the demand filters", () => {
    expect(
      buildPpcHref({
        subpluginId: "demand",
        branch: "01",
        demandSearch: "90262910",
        demandStatus: "at_risk",
      }),
    ).toBe("/apps/production-control/demand?branch=01&q=90262910&status=at_risk");
  });

  it("reads materials detail identity from the query string", () => {
    expect(
      readMaterialsDetailDeepLink("?branch=01&request=SC001&item=01"),
    ).toEqual({
      requestNumber: "SC001",
      requestItem: "01",
    });
    expect(readMaterialsDetailDeepLink("?branch=01")).toEqual({
      requestNumber: null,
      requestItem: null,
    });
  });

  it("reads materials search and request identity from the deep link", () => {
    const route = parsePpcPath(
      "/apps/production-control/materials",
      "?branch=01&q=10020113&issue=shortage&request=SC001&item=01",
      "02",
    );
    expect(route.subpluginId).toBe("materials");
    expect(route.materialsSearch).toBe("10020113");
    expect(route.materialsIssue).toBe("shortage");
    expect(route.requestNumber).toBe("SC001");
    expect(route.requestItem).toBe("01");
  });

  it("serializes the materials deep link", () => {
    expect(
      buildPpcHref({
        subpluginId: "materials",
        branch: "01",
        materialsSearch: "10020113",
        materialsIssue: "excess",
        requestNumber: "SC001",
        requestItem: "01",
      }),
    ).toBe(
      "/apps/production-control/materials?branch=01&q=10020113&issue=excess&request=SC001&item=01",
    );
  });

  it("reads delivery map search from the deep link", () => {
    const route = parsePpcPath("/apps/production-control/delivery-map", "?branch=01&q=90262910");
    expect(route.subpluginId).toBe("delivery-map");
    expect(route.deliveryMapSearch).toBe("90262910");
  });

  it("serializes the delivery map deep link", () => {
    expect(
      buildPpcHref({
        subpluginId: "delivery-map",
        branch: "01",
        deliveryMapSearch: "107376",
      }),
    ).toBe("/apps/production-control/delivery-map?branch=01&q=107376");
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
