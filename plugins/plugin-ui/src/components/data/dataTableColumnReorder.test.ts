import { describe, expect, it } from "vitest";

import {
  reorderColumnKeys,
  reorderColumnKeysWithEdge,
  resolveColumnDropEdge,
} from "./dataTableColumnReorder";

describe("dataTableColumnReorder", () => {
  it("reorderColumnKeys move a chave para o índice do alvo", () => {
    expect(reorderColumnKeys(["a", "b", "c"], "c", "a")).toEqual(["c", "a", "b"]);
    expect(reorderColumnKeys(["a", "b", "c"], "a", "c")).toEqual(["b", "c", "a"]);
  });

  it("reorderColumnKeysWithEdge respeita before/after", () => {
    expect(reorderColumnKeysWithEdge(["a", "b", "c"], "c", "a", "before")).toEqual([
      "c",
      "a",
      "b",
    ]);
    expect(reorderColumnKeysWithEdge(["a", "b", "c"], "c", "a", "after")).toEqual([
      "a",
      "c",
      "b",
    ]);
    expect(reorderColumnKeysWithEdge(["a", "b", "c"], "a", "c", "before")).toEqual([
      "b",
      "a",
      "c",
    ]);
    expect(reorderColumnKeysWithEdge(["a", "b", "c"], "a", "c", "after")).toEqual([
      "b",
      "c",
      "a",
    ]);
  });

  it("resolveColumnDropEdge usa o centro do header", () => {
    const rect = { left: 100, width: 100 } as DOMRect;
    expect(resolveColumnDropEdge(120, rect)).toBe("before");
    expect(resolveColumnDropEdge(160, rect)).toBe("after");
    expect(resolveColumnDropEdge(10, { left: 0, width: 0 } as DOMRect)).toBe("before");
    expect(resolveColumnDropEdge(Number.NaN, rect)).toBe("before");
  });
});
