import { describe, expect, it } from "vitest";
import { buildScPcConversionParams } from "./scPcConversionApi";
import { buildPluginPath, resolveActiveNavId, resolvePluginRoute } from "../../app/pluginRoutes";

describe("GLPI #635: conversion clock starts at last valid SCR approval", () => {
  it("registers a canonical route within the purchase requests section", () => {
    const path = buildPluginPath("sc_pc_conversion");
    expect(path).toBe("/apps/supplies/purchase-requests/sc-pc-conversion");
    expect(resolvePluginRoute(path).view).toBe("sc_pc_conversion");
    expect(resolveActiveNavId("sc_pc_conversion")).toBe("purchase_requests");
  });

  it("forwards explicit authorized unit and bounded period to the BFF", () => {
    const params = buildScPcConversionParams({
      branches: ["01", "02", "all", "03"],
      dateFrom: "2026-10-01",
      dateTo: "2026-10-31",
      requestNumber: "171945",
      page: 2,
    });
    expect(params.getAll("branch")).toEqual(["01", "02"]);
    expect(params.get("date_from")).toBe("2026-10-01");
    expect(params.get("date_to")).toBe("2026-10-31");
    expect(params.get("request_number")).toBe("171945");
    expect(params.get("page")).toBe("2");
    expect(params.get("page_size")).toBe("25");
  });
});
