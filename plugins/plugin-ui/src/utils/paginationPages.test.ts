import { describe, expect, it } from "vitest";

import {
  buildVisiblePageItems,
  parsePageJumpInput,
} from "./paginationPages";

describe("paginationPages", () => {
  it("buildVisiblePageItems inclui ellipsis em listas longas", () => {
    expect(buildVisiblePageItems(5, 12)).toEqual([1, "ellipsis", 4, 5, 6, "ellipsis", 12]);
  });

  it("parsePageJumpInput valida intervalo", () => {
    expect(parsePageJumpInput("3", 10)).toEqual({ ok: true, page: 3 });
    expect(parsePageJumpInput("0", 10)).toEqual({ ok: false, reason: "below_min" });
    expect(parsePageJumpInput("11", 10)).toEqual({ ok: false, reason: "above_max" });
  });
});
