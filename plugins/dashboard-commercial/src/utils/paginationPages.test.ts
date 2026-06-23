import { describe, expect, it } from "vitest";

import { buildVisiblePageItems } from "./paginationPages";

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
