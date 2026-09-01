import { describe, expect, it } from "vitest";

import { buildFinancialHref, isBranch, parseFinancialPath } from "./routeParser";

describe("parseFinancialPath", () => {
  it("defaults the empty base path to home and the stored branch", () => {
    const route = parseFinancialPath("/apps/financial", "", "02");
    expect(route.subpluginId).toBe("home");
    expect(route.branch).toBe("02");
  });

  it("reads delinquency filters from the shareable URL", () => {
    const route = parseFinancialPath(
      "/apps/financial/delinquency",
      "?branch=all&startDate=2026-01-01&endDate=2026-08-22&client=000001|01&customer=000001&customerStore=01&status=late&delayRange=ATRASO_1_A_5_DIAS&page=3",
      "01",
    );
    expect(route.subpluginId).toBe("delinquency");
    expect(route.branch).toBe("all");
    expect(route.startDate).toBe("2026-01-01");
    expect(route.endDate).toBe("2026-08-22");
    expect(route.clientKey).toBe("000001|01");
    expect(route.customerCode).toBe("000001");
    expect(route.customerStore).toBe("01");
    expect(route.status).toBe("late");
    expect(route.delayRange).toBe("ATRASO_1_A_5_DIAS");
    expect(route.page).toBe(3);
  });

  it("reads billing granularity from the shareable URL", () => {
    const route = parseFinancialPath(
      "/apps/financial/billing",
      "?branch=01&startDate=2026-08-01&endDate=2026-08-31&granularity=week",
      "02",
    );
    expect(route.subpluginId).toBe("billing");
    expect(route.granularity).toBe("week");
  });

  it("drops an invalid title status instead of forwarding it to the API", () => {
    const route = parseFinancialPath("/apps/financial/delinquency", "?status=pendente", "01");
    expect(route.status).toBeNull();
  });

  it("reads the focused expense month from the shareable URL", () => {
    const route = parseFinancialPath(
      "/apps/financial/cost-centers",
      "?branch=01&month=2026-09&costCenter=1101&excludeMp=1",
      "01",
    );
    expect(route.subpluginId).toBe("cost-centers");
    expect(route.month).toBe("2026-09");
    expect(route.costCenter).toBe("1101");
    expect(route.excludeMp).toBe(true);
  });

  it("drops a malformed month instead of forwarding it to the API", () => {
    expect(parseFinancialPath("/apps/financial/cost-centers", "?month=2026-13", "01").month).toBeNull();
    expect(parseFinancialPath("/apps/financial/cost-centers", "?month=2026-9", "01").month).toBeNull();
    expect(parseFinancialPath("/apps/financial/cost-centers", "?month=2026-00", "01").month).toBeNull();
    expect(
      parseFinancialPath("/apps/financial/cost-centers", "?month=2026-09-01", "01").month,
    ).toBeNull();
  });

  it("ignores malformed dates", () => {
    const route = parseFinancialPath(
      "/apps/financial/cost-centers",
      "?startDate=01%2F08%2F2026&endDate=",
      "01",
    );
    expect(route.startDate).toBeNull();
    expect(route.endDate).toBeNull();
  });
});

describe("buildFinancialHref", () => {
  it("keeps home on the plugin base path", () => {
    expect(buildFinancialHref({ subpluginId: "home", branch: "01" })).toBe(
      "/apps/financial?branch=01",
    );
  });

  it("serializes delinquency client filter", () => {
    expect(
      buildFinancialHref({
        subpluginId: "delinquency",
        branch: "all",
        clientKey: "000001|01",
      }),
    ).toBe("/apps/financial/delinquency?branch=all&client=000001%7C01");
  });

  it("serializes billing granularity", () => {
    expect(
      buildFinancialHref({
        subpluginId: "billing",
        branch: "01",
        granularity: "week",
      }),
    ).toBe("/apps/financial/billing?branch=01&granularity=week");
  });

  it("serializes cost-center filters", () => {
    expect(
      buildFinancialHref({
        subpluginId: "cost-centers",
        branch: "02",
        costCenter: "1101",
        supplierCode: "000045",
        supplierStore: "01",
        page: 2,
      }),
    ).toBe(
      "/apps/financial/cost-centers?branch=02&costCenter=1101&supplier=000045&supplierStore=01&page=2",
    );
  });

  it("serializes the expense month alongside the inherited filters", () => {
    expect(
      buildFinancialHref({
        subpluginId: "cost-centers",
        branch: "01",
        month: "2026-09",
        costCenter: "1101",
        supplierCode: "000045",
        supplierStore: "01",
        excludeMp: true,
      }),
    ).toBe(
      "/apps/financial/cost-centers?branch=01&costCenter=1101&supplier=000045&supplierStore=01&excludeMp=1&month=2026-09",
    );
  });
});

describe("isBranch", () => {
  it("accepts TOTVS branches and the consolidated alias", () => {
    expect(isBranch("01")).toBe(true);
    expect(isBranch("all")).toBe(true);
    expect(isBranch("99")).toBe(false);
  });
});
