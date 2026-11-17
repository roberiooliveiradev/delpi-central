import { describe, expect, it } from "vitest";
import { buildFreightImpactParams } from "./api";
describe("freight impact query", () => {
  it("uses concrete deduplicated branches and dates", () => {
    const params = buildFreightImpactParams({ branches: ["01","01","all","02"], dateFrom:"2026-01-01", dateTo:"2026-11-17", page: 2 });
    expect(params.getAll("branch")).toEqual(["01","02"]);
    expect(params.get("date_from")).toBe("2026-01-01");
    expect(params.get("date_to")).toBe("2026-11-17");
    expect(params.get("page")).toBe("2");
  });
});
