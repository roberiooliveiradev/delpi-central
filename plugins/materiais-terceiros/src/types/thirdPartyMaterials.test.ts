import { describe, expect, it } from "vitest";

import { EMPTY_QUERY, hasUsefulScope } from "./thirdPartyMaterials";

describe("hasUsefulScope", () => {
  it("exige filial + critério", () => {
    expect(hasUsefulScope({ ...EMPTY_QUERY, branch: "01" })).toBe(false);
    expect(hasUsefulScope({ ...EMPTY_QUERY, branch: "01", product: "10211413" })).toBe(true);
    expect(hasUsefulScope({ ...EMPTY_QUERY, branch: "01", customerReference: "10018137" })).toBe(
      true,
    );
    expect(hasUsefulScope({ ...EMPTY_QUERY, branch: "01", onlyWithBalance: true })).toBe(true);
    expect(hasUsefulScope({ ...EMPTY_QUERY, product: "10211413" })).toBe(false);
  });
});
