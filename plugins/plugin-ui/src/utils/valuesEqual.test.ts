import { describe, expect, it } from "vitest";

import { valuesEqual, shouldShowDirtySave } from "./valuesEqual";

describe("valuesEqual", () => {
  it("compara primitivos e objetos com chaves em ordem diferente", () => {
    expect(valuesEqual(1, 1)).toBe(true);
    expect(valuesEqual({ a: 1, b: 2 }, { b: 2, a: 1 })).toBe(true);
    expect(valuesEqual({ a: 1 }, { a: 2 })).toBe(false);
    expect(valuesEqual(["x", "y"], ["x", "y"])).toBe(true);
    expect(valuesEqual(["x", "y"], ["y", "x"])).toBe(false);
  });
});

describe("shouldShowDirtySave", () => {
  it("só exibe salvar com dirty ou enquanto saving", () => {
    expect(shouldShowDirtySave(false)).toBe(false);
    expect(shouldShowDirtySave(true)).toBe(true);
    expect(shouldShowDirtySave(false, true)).toBe(true);
  });
});
