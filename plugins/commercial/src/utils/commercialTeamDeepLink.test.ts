import { describe, expect, it } from "vitest";

import {
  normalizeCommercialTeamView,
  parseCommercialTeamView,
} from "./commercialTeamDeepLink";

describe("commercialTeamDeepLink", () => {
  it("normaliza view list|org", () => {
    expect(normalizeCommercialTeamView("org")).toBe("org");
    expect(normalizeCommercialTeamView("LIST")).toBe("list");
    expect(normalizeCommercialTeamView("x")).toBe("list");
  });

  it("parseia search string", () => {
    expect(parseCommercialTeamView("?view=org")).toBe("org");
    expect(parseCommercialTeamView("")).toBe("list");
  });
});
