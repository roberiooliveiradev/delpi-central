import { describe, expect, it } from "vitest";

import { formatDecimalString, formatDecimalStringFixed } from "./formatDecimalString";

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

describe("formatDecimalStringFixed", () => {
  it("always shows three decimal places in pt-BR", () => {
    expect(formatDecimalStringFixed("1", 3)).toBe("1,000");
    expect(formatDecimalStringFixed("1.2", 3)).toBe("1,200");
    expect(formatDecimalStringFixed("1.23", 3)).toBe("1,230");
    expect(formatDecimalStringFixed("1.234", 3)).toBe("1,234");
    expect(formatDecimalStringFixed("1234.5", 3)).toBe("1.234,500");
    expect(formatDecimalStringFixed("0", 3)).toBe("0,000");
  });

  it("rounds only for display when more than three places", () => {
    expect(formatDecimalStringFixed("1.2345", 3)).toBe("1,235");
    expect(formatDecimalStringFixed("1.2344", 3)).toBe("1,234");
  });

  it("handles negatives and invalid", () => {
    expect(formatDecimalStringFixed("-1.2", 3)).toBe("-1,200");
    expect(formatDecimalStringFixed("", 3)).toBe("—");
    expect(formatDecimalStringFixed("abc", 3)).toBe("—");
  });
});
