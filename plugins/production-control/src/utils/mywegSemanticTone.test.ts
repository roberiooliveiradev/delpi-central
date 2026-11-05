import { describe, expect, it } from "vitest";

import {
  deltaToneClass,
  movementBadgeClass,
  situationBadgeClass,
  toneFromSituation,
} from "./mywegSemanticTone";

describe("mywegSemanticTone", () => {
  it("mapeia situações para tom semântico", () => {
    expect(toneFromSituation("increased")).toBe("up");
    expect(toneFromSituation("decreased")).toBe("down");
    expect(toneFromSituation("unchanged")).toBe("neutral");
    expect(toneFromSituation("stable_with_date_changes")).toBe("info");
  });

  it("aplica classes de badge e delta", () => {
    expect(situationBadgeClass("increased")).toContain("movement--up");
    expect(situationBadgeClass("decreased")).toContain("movement--down");
    expect(movementBadgeClass("appeared")).toContain("movement--up");
    expect(movementBadgeClass("disappeared")).toContain("movement--down");
    expect(deltaToneClass("increased")).toContain("delta--up");
    expect(deltaToneClass("decreased")).toContain("delta--down");
  });
});
