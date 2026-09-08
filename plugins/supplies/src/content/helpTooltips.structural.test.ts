import { describe, expect, it } from "vitest";

import { SP_HELP } from "./helpTooltips";

function collectStrings(value: unknown, acc: string[] = []): string[] {
  if (typeof value === "string") {
    acc.push(value);
    return acc;
  }
  if (value && typeof value === "object") {
    for (const nested of Object.values(value as Record<string, unknown>)) {
      collectStrings(nested, acc);
    }
  }
  return acc;
}

describe("helpTooltips", () => {
  it("keeps required shell help keys", () => {
    expect(SP_HELP.coexistence.length).toBeGreaterThan(20);
    expect(SP_HELP.homeVsOverview.length).toBeGreaterThan(20);
    expect(SP_HELP.forbiddenUnit.length).toBeGreaterThan(20);
    expect(SP_HELP.shell.navHome).toBeTruthy();
    expect(SP_HELP.shell.navOverview).toBeTruthy();
  });

  it("does not leak technical identifiers in help copy", () => {
    const texts = collectStrings(SP_HELP);
    for (const text of texts) {
      expect(text).not.toMatch(/operationId|\/apps\/supplies-api|GET \//);
    }
  });
});
