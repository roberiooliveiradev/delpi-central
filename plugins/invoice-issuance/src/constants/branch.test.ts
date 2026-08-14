import { describe, expect, it } from "vitest";
import { branchFromPathname, branchLabel } from "./branch";

describe("branchFromPathname", () => {
  it("detecta filial-01 e filial-02", () => {
    expect(branchFromPathname("/apps/invoice-issuance/filial-01")).toBe("01");
    expect(branchFromPathname("/apps/invoice-issuance/filial-02")).toBe("02");
    expect(branchFromPathname("/apps/invoice-issuance")).toBeNull();
  });
});

describe("branchLabel", () => {
  it("rótula SC e ES", () => {
    expect(branchLabel("01")).toContain("SC");
    expect(branchLabel("02")).toContain("ES");
  });
});
