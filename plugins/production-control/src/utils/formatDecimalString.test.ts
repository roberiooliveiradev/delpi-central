import { describe, expect, it } from "vitest";

import { formatDecimalString } from "./formatDecimalString";

describe("formatDecimalString", () => {
  it("formats integer and fractional strings without float", () => {
    expect(formatDecimalString("745746")).toBe("745.746");
    expect(formatDecimalString("745.746")).toBe("745,746");
    expect(formatDecimalString("0.000001")).toBe("0,000001");
  });

  it("keeps empty as dash", () => {
    expect(formatDecimalString("")).toBe("—");
    expect(formatDecimalString(null)).toBe("—");
  });
});
