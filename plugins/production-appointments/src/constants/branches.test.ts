import { describe, expect, it } from "vitest";

import {
  PRODUCTION_APPOINTMENTS_BASE_PATH,
  branchRouteFromPathname,
  totvsBranchFromRoute,
} from "./branches";

describe("branches", () => {
  it("resolve SC/ES a partir do path", () => {
    expect(branchRouteFromPathname(`${PRODUCTION_APPOINTMENTS_BASE_PATH}/sc`)).toBe(
      "SC",
    );
    expect(branchRouteFromPathname(`${PRODUCTION_APPOINTMENTS_BASE_PATH}/es`)).toBe(
      "ES",
    );
  });

  it("mapeia TOTVS", () => {
    expect(totvsBranchFromRoute("SC")).toBe("01");
    expect(totvsBranchFromRoute("ES")).toBe("02");
  });
});
