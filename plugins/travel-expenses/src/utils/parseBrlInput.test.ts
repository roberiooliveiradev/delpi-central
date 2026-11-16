import { describe, expect, it } from "vitest";
import { parseBrlInput } from "./parseBrlInput";

describe("parseBrlInput: ticket #1597", () => {
  it.each([
    ["R$324,00", 324],
    ["R$ 324,00", 324],
    ["324,00", 324],
    ["324.00", 324],
    ["R$ 1.234,56", 1234.56],
    ["0", 0],
  ])("parses %s into %s", (text, expected) => {
    expect(parseBrlInput(text)).toBe(expected);
  });

  it.each(["", "R$ xxx", "NaN", "1,000.00", "-1", "1.2.3"])(
    "rejects invalid value %s", (text) => {
      expect(parseBrlInput(text)).toBeNull();
    },
  );
});
