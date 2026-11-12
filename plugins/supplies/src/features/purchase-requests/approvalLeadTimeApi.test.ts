import { describe, expect, it } from "vitest";
import { buildApprovalLeadTimeParams } from "./approvalLeadTimeApi";
import { buildPluginPath, resolveActiveNavId, resolvePluginRoute } from "../../app/pluginRoutes";

describe("SCR-only approval lead time", () => {
  it("links from purchase requests and groups it in the correct navigation", () => {
    const path = buildPluginPath("approval_lead_time");
    expect(path).toBe("/apps/supplies/purchase-requests/approval-lead-time");
    expect(resolvePluginRoute(path).view).toBe("approval_lead_time");
    expect(resolveActiveNavId("approval_lead_time")).toBe("purchase_requests");
  });

  it("queries BFF with explicit branches and bounded filters", () => {
    const params = buildApprovalLeadTimeParams({
      branches: ["01", "02", "all", "03"],
      dateFrom: "2026-01-01",
      dateTo: "2026-11-12",
      requestNumber: "171945",
      page: 2,
    });
    expect(params.getAll("branch")).toEqual(["01", "02"]);
    expect(params.get("request_number")).toBe("171945");
    expect(params.get("page")).toBe("2");
    expect(params.get("page_size")).toBe("25");
  });
});
