import { describe, expect, it } from "vitest";

import { formatOpQuantity } from "./formatOpQuantity";

describe("formatOpQuantity", () => {
  it("always uses 3 decimal places for milheiro", () => {
    expect(formatOpQuantity(0.02)).toBe("0,020");
    expect(formatOpQuantity(0.1)).toBe("0,100");
    expect(formatOpQuantity(12)).toBe("12,000");
  });

  it("returns empty marker for missing values", () => {
    expect(formatOpQuantity(null)).toBe("—");
    expect(formatOpQuantity(undefined)).toBe("—");
  });
});
