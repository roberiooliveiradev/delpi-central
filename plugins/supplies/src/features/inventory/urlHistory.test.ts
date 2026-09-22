import { describe, expect, it } from "vitest";

import {
  buildUrlSearch,
  parseQueryFromSearch,
  sameInventoryQuery,
} from "./query";
import { createDefaultQuery } from "./query";

describe("inventory URL popstate rehydration (pure)", () => {
  it("estado A → B → parse restaura A", () => {
    const a = {
      ...createDefaultQuery(),
      branches: ["01"],
      warehouse: "",
      sort: "stock_value_desc" as const,
      page: 1,
    };
    const b = {
      ...createDefaultQuery(),
      branches: ["02"],
      warehouse: "25",
      sort: "quantity_asc" as const,
      page: 2,
      page_size: 100,
    };
    const restoredA = parseQueryFromSearch(buildUrlSearch(a), ["01", "02"]);
    const restoredB = parseQueryFromSearch(buildUrlSearch(b), ["01", "02"]);
    expect(sameInventoryQuery(restoredA, a)).toBe(true);
    expect(sameInventoryQuery(restoredB, b)).toBe(true);
    expect(sameInventoryQuery(restoredA, restoredB)).toBe(false);
  });
});
