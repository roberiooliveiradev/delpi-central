import { describe, expect, it } from "vitest";

import {
  filterIncompleteSetsByRootProduct,
  matchesRootProductQuery,
  normalizeRootProductQuery,
} from "./filterIncompleteSetsByRootProduct";
import type { IncompleteOrderSetItem } from "../types";

const rows: IncompleteOrderSetItem[] = [
  {
    id: "1",
    kind: "incomplete-order-sets",
    severity: "critical",
    branch: "01",
    set_key: "10840401",
    set_number: "108404",
    set_item: "01",
    root_code: "80123456",
    root_description: "TRANSFORMADOR XYZ",
    root_order: "10840401",
    due_date: null,
    issued_at: null,
    order_count: 3,
    open_order_count: 2,
    expected_component_count: 2,
    created_component_count: 1,
    missing_count: 1,
    extra_count: 0,
    missing_components: [],
    extra_components: [],
  },
  {
    id: "2",
    kind: "incomplete-order-sets",
    severity: "attention",
    branch: "01",
    set_key: "11220701",
    set_number: "112207",
    set_item: "01",
    root_code: "90998877",
    root_description: "REATOR ABC",
    root_order: null,
    due_date: null,
    issued_at: null,
    order_count: 2,
    open_order_count: 2,
    expected_component_count: 1,
    created_component_count: 2,
    missing_count: 0,
    extra_count: 1,
    missing_components: [],
    extra_components: [],
  },
];

describe("filterIncompleteSetsByRootProduct", () => {
  it("normaliza a query", () => {
    expect(normalizeRootProductQuery("  8012  ")).toBe("8012");
  });

  it("casa por prefixo do código", () => {
    expect(matchesRootProductQuery(rows[0]!, "8012")).toBe(true);
    expect(matchesRootProductQuery(rows[1]!, "8012")).toBe(false);
  });

  it("casa por trecho da descrição", () => {
    expect(matchesRootProductQuery(rows[1]!, "reator")).toBe(true);
  });

  it("query vazia devolve todos", () => {
    expect(filterIncompleteSetsByRootProduct(rows, "  ")).toHaveLength(2);
  });

  it("filtra a lista", () => {
    expect(filterIncompleteSetsByRootProduct(rows, "90").map((row) => row.id)).toEqual(["2"]);
  });
});
