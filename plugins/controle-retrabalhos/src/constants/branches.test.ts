import { describe, expect, it } from "vitest";

import {
  branchRouteFromPathname,
  DEFAULT_BRANCH_ROUTE,
  totvsBranchFromRoute,
  TOTVS_BRANCH_BY_ROUTE,
} from "../constants/branches";

describe("branches", () => {
  it("maps /sc to filial 01", () => {
    expect(branchRouteFromPathname("/apps/controle-retrabalhos/sc")).toBe("SC");
    expect(totvsBranchFromRoute("SC")).toBe("01");
  });

  it("maps /es to filial 02", () => {
    expect(branchRouteFromPathname("/apps/controle-retrabalhos/es")).toBe("ES");
    expect(totvsBranchFromRoute("ES")).toBe("02");
  });

  it("falls back to SC when route is missing or unknown", () => {
    expect(branchRouteFromPathname()).toBe(DEFAULT_BRANCH_ROUTE);
    expect(branchRouteFromPathname("/apps/controle-retrabalhos")).toBe("SC");
    expect(branchRouteFromPathname("/apps/controle-retrabalhos/matriz")).toBe("SC");
  });

  it("keeps only SC and ES in TOTVS mapping", () => {
    expect(TOTVS_BRANCH_BY_ROUTE).toEqual({ SC: "01", ES: "02" });
  });
});
