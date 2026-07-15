import { describe, expect, it } from "vitest";

import {
  branchRouteFromPathname,
  totvsBranchFromRoute,
} from "./branches";

describe("branches", () => {
  it("mapeia rotas /sc e /es para filiais TOTVS", () => {
    expect(branchRouteFromPathname("/apps/scrap-monitoring/sc")).toBe("SC");
    expect(branchRouteFromPathname("/apps/scrap-monitoring/es")).toBe("ES");
    expect(totvsBranchFromRoute("SC")).toBe("01");
    expect(totvsBranchFromRoute("ES")).toBe("02");
  });
});
