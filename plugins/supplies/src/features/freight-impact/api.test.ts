import { describe, expect, it } from "vitest";
import { buildFreightImpactParams } from "./api";

describe("freight impact query", () => {
  it("uses concrete unique branches, dates and the official financial filters", () => {
    const params = buildFreightImpactParams({
      branches: ["01", "01", "all", "02"],
      dateFrom: "2026-11-01",
      dateTo: "2026-11-17",
      dateMode: "issue",
      situation: "above_limit",
      page: 2,
    });
    expect(params.getAll("branch")).toEqual(["01", "02"]);
    expect(params.get("date_from")).toBe("2026-11-01");
    expect(params.get("date_to")).toBe("2026-11-17");
    expect(params.get("date_mode")).toBe("issue");
    expect(params.get("situation")).toBe("above_limit");
    expect(params.get("page")).toBe("2");
  });
  it("also supports comparing by entry date", () => {
    const params = buildFreightImpactParams({
      branches: ["02"],
      dateFrom: "2026-10-01",
      dateTo: "2026-10-31",
      dateMode: "entry",
      situation: "all",
      page: 1,
    });
    expect(params.get("date_mode")).toBe("entry");
    expect(params.getAll("branch")).toEqual(["02"]);
  });
});
