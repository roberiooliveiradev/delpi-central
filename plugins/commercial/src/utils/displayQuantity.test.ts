import { describe, expect, it } from "vitest";

import {
  formatDisplayQuantity,
  resolveDisplayQuantity,
} from "./displayQuantity";

describe("resolveDisplayQuantity", () => {
  it("keeps catalog MI unchanged", () => {
    expect(resolveDisplayQuantity(1.5, "MI", "catalog")).toEqual({
      value: 1.5,
      unit: "MI",
      converted: false,
    });
  });

  it("converts only MI to pieces", () => {
    expect(resolveDisplayQuantity(2, "MI", "pieces")).toEqual({
      value: 2000,
      unit: "PC",
      converted: true,
    });
    expect(resolveDisplayQuantity(2, "PC", "pieces")).toEqual({
      value: 2,
      unit: "PC",
      converted: false,
    });
  });

  it("formats with three decimal places", () => {
    expect(formatDisplayQuantity(1.2345, "MI", "catalog")).toBe("1,235 MI");
  });

  it("omits unit suffix when UM is missing", () => {
    expect(formatDisplayQuantity(10, "", "pieces")).toBe("10,000");
    expect(formatDisplayQuantity(10, null, "catalog")).toBe("10,000");
  });
});
