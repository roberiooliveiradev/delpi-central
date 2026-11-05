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

  it("reads report id from the reports deep link", () => {
    const route = parsePpcPath(
      "/apps/production-control/reports",
      "?branch=01&report=stock-balances",
      "02",
    );
    expect(route.subpluginId).toBe("reports");
    expect(route.branch).toBe("01");
    expect(route.reportId).toBe("stock-balances");
  });

  it("reads the production-orders report deep link", () => {
    const route = parsePpcPath(
      "/apps/production-control/reports",
      "?branch=01&report=production-orders",
      "02",
    );
    expect(route.subpluginId).toBe("reports");
    expect(route.reportId).toBe("production-orders");
  });

  it("ignores unknown report ids", () => {
    const route = parsePpcPath(
      "/apps/production-control/reports",
      "?branch=01&report=unknown",
      "01",
    );
    expect(route.reportId).toBeNull();
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

  it("serializes the report deep link", () => {
    expect(
      buildPpcHref({
        subpluginId: "reports",
        branch: "02",
        reportId: "stock-balances",
      }),
    ).toBe("/apps/production-control/reports?branch=02&report=stock-balances");
  });

  it("serializes the production-orders report deep link", () => {
    expect(
      buildPpcHref({
        subpluginId: "reports",
        branch: "01",
        reportId: "production-orders",
      }),
    ).toBe("/apps/production-control/reports?branch=01&report=production-orders");
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

  it("reads the finished-product shortage consult from the deep link", () => {
    const route = parsePpcPath(
      "/apps/production-control/materials",
      "?branch=01&issue=pa-shortage&q=90263114&status=shortage",
      "02",
    );
    expect(route.subpluginId).toBe("materials");
    expect(route.materialsIssue).toBe("pa-shortage");
    expect(route.materialsSearch).toBe("90263114");
    expect(route.materialsStatus).toBe("shortage");
  });

  it("serializes the finished-product shortage consult", () => {
    expect(
      buildPpcHref({
        subpluginId: "materials",
        branch: "01",
        materialsIssue: "pa-shortage",
        materialsSearch: "90263114",
        materialsStatus: "no_commitment",
      }),
    ).toBe(
      "/apps/production-control/materials?branch=01&q=90263114&issue=pa-shortage&status=no_commitment",
    );
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

  it("serializes the product 3D models workspace", () => {
    expect(buildPpcHref({ subpluginId: "product-models", branch: "01" })).toBe(
      "/apps/production-control/product-models?branch=01",
    );
    const route = parsePpcPath("/apps/production-control/product-models", "?branch=02", "01");
    expect(route.subpluginId).toBe("product-models");
    expect(route.branch).toBe("02");
  });
});

describe("line feeder deep link", () => {
  it("lê corte, bancada, situação e lista da URL", () => {
    const route = parsePpcPath(
      "/apps/production-control/line-feeder",
      "?branch=02&cutoffDate=2026-09-22&cutoffTime=14:30&ct=CT-02&status=at_risk&plan=abc",
      "01",
    );
    expect(route.subpluginId).toBe("line-feeder");
    expect(route.branch).toBe("02");
    expect(route.cutoffDate).toBe("2026-09-22");
    expect(route.cutoffTime).toBe("14:30");
    expect(route.workCenter).toBe("CT-02");
    expect(route.lineFeederStatus).toBe("at_risk");
    expect(route.planId).toBe("abc");
  });

  it("descarta data, hora e situação inválidas", () => {
    const route = parsePpcPath(
      "/apps/production-control/line-feeder",
      "?branch=01&cutoffDate=22/09/2026&cutoffTime=99:99&status=banana",
      "01",
    );
    expect(route.cutoffDate).toBeNull();
    expect(route.cutoffTime).toBeNull();
    expect(route.lineFeederStatus).toBeNull();
  });

  it("não confunde a situação do material com a da demanda", () => {
    const route = parsePpcPath(
      "/apps/production-control/line-feeder",
      "?branch=01&status=late",
      "01",
    );
    expect(route.lineFeederStatus).toBeNull();
    expect(route.demandStatus).toBe("late");
  });

  it("monta o href do alimentador preservando o corte", () => {
    const href = buildPpcHref({
      subpluginId: "line-feeder",
      branch: "01",
      cutoffDate: "2026-09-22",
      cutoffTime: "14:00",
      workCenter: "CT-01",
      lineFeederStatus: "to_pick",
      planId: "plan-1",
    });
    expect(href).toBe(
      "/apps/production-control/line-feeder?branch=01&ct=CT-01&cutoffDate=2026-09-22&cutoffTime=14%3A00&status=to_pick&plan=plan-1",
    );
  });

  it("reads myweg-needs filters from the deep link", () => {
    const route = parsePpcPath(
      "/apps/production-control/myweg-needs",
      "?branch=02&batch=abc-1&q=parafuso&remessaFrom=2026-11-01&remessaTo=2026-11-30&page=3",
      "01",
    );
    expect(route.subpluginId).toBe("myweg-needs");
    expect(route.branch).toBe("02");
    expect(route.mywegNeedsBatchId).toBe("abc-1");
    expect(route.mywegNeedsSearch).toBe("parafuso");
    expect(route.mywegNeedsRemessaFrom).toBe("2026-11-01");
    expect(route.mywegNeedsRemessaTo).toBe("2026-11-30");
    expect(route.mywegNeedsPage).toBe(3);
    expect(route.mywegNeedsView).toBeNull();
  });

  it("reads myweg-needs view=compare and defaults absent view to null", () => {
    const compare = parsePpcPath(
      "/apps/production-control/myweg-needs",
      "?branch=02&view=compare",
      "02",
    );
    expect(compare.mywegNeedsView).toBe("compare");
    const needs = parsePpcPath(
      "/apps/production-control/myweg-needs",
      "?branch=02&view=needs",
      "02",
    );
    expect(needs.mywegNeedsView).toBe("needs");
    const unknown = parsePpcPath(
      "/apps/production-control/myweg-needs",
      "?branch=02&view=other",
      "02",
    );
    expect(unknown.mywegNeedsView).toBeNull();
  });

  it("builds myweg-needs href with shareable filters", () => {
    const href = buildPpcHref({
      subpluginId: "myweg-needs",
      branch: "02",
      mywegNeedsBatchId: "batch-9",
      mywegNeedsSearch: "doc-1",
      mywegNeedsRemessaFrom: "2026-11-10",
      mywegNeedsPage: 2,
    });
    expect(href).toBe(
      "/apps/production-control/myweg-needs?branch=02&q=doc-1&batch=batch-9&remessaFrom=2026-11-10&page=2",
    );
  });

  it("builds myweg-needs href with view=compare", () => {
    const href = buildPpcHref({
      subpluginId: "myweg-needs",
      branch: "02",
      mywegNeedsView: "compare",
    });
    expect(href).toBe("/apps/production-control/myweg-needs?branch=02&view=compare");
  });

  it("reads and builds analysis=products for compare", () => {
    const route = parsePpcPath(
      "/apps/production-control/myweg-needs",
      "?branch=02&view=compare&analysis=products",
    );
    expect(route.mywegNeedsAnalysis).toBe("products");
    const href = buildPpcHref({
      subpluginId: "myweg-needs",
      branch: "02",
      mywegNeedsView: "compare",
      mywegNeedsAnalysis: "products",
    });
    expect(href).toContain("view=compare");
    expect(href).toContain("analysis=products");
  });
});
