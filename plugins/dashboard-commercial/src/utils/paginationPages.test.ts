import { describe, expect, it } from "vitest";

import { buildVisiblePageItems, parsePageJumpInput } from "./paginationPages";

describe("buildVisiblePageItems", () => {
  it("retorna todas as páginas quando total é pequeno", () => {
    expect(buildVisiblePageItems(2, 5)).toEqual([1, 2, 3, 4, 5]);
  });

  it("insere reticências no meio de listas longas", () => {
    expect(buildVisiblePageItems(8, 20)).toEqual([
      1,
      "ellipsis",
      7,
      8,
      9,
      "ellipsis",
      20,
    ]);
  });
});

describe("parsePageJumpInput", () => {
  it("aceita página válida", () => {
    expect(parsePageJumpInput("12", 34)).toEqual({ ok: true, page: 12 });
    expect(parsePageJumpInput(" 3 ", 10)).toEqual({ ok: true, page: 3 });
  });

  it("rejeita entradas inválidas", () => {
    expect(parsePageJumpInput("", 34)).toEqual({ ok: false, reason: "empty" });
    expect(parsePageJumpInput("abc", 34)).toEqual({
      ok: false,
      reason: "invalid",
    });
    expect(parsePageJumpInput("0", 34)).toEqual({
      ok: false,
      reason: "below_min",
    });
    expect(parsePageJumpInput("35", 34)).toEqual({
      ok: false,
      reason: "above_max",
    });
  });
});
