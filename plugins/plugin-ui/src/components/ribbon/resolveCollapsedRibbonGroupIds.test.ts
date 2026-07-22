import { describe, expect, it } from "vitest";

import {
  resolveCollapsedRibbonGroupIds,
  sumRibbonGroupsWidth,
  type RibbonGroupSize,
} from "./resolveCollapsedRibbonGroupIds";

function groups(widths: Array<[string, number, number]>): RibbonGroupSize[] {
  return widths.map(([id, expandedWidth, collapsedWidth], order) => ({
    id,
    expandedWidth,
    collapsedWidth,
    order,
  }));
}

describe("resolveCollapsedRibbonGroupIds", () => {
  it("não colapsa quando tudo cabe", () => {
    const list = groups([
      ["a", 100, 56],
      ["b", 100, 56],
      ["c", 100, 56],
    ]);
    // 300 + 2*8 = 316
    expect([...resolveCollapsedRibbonGroupIds(list, 400, 8)]).toEqual([]);
  });

  it("colapsa da direita para a esquerda", () => {
    const list = groups([
      ["a", 120, 56],
      ["b", 120, 56],
      ["c", 120, 56],
    ]);
    // full 360+16=376; collapse c → 120+120+56+16=312; collapse b,c → 120+56+56+16=248
    const one = resolveCollapsedRibbonGroupIds(list, 330, 8);
    expect([...one]).toEqual(["c"]);

    const two = resolveCollapsedRibbonGroupIds(list, 260, 8);
    expect([...two].sort()).toEqual(["b", "c"]);
  });

  it("sumRibbonGroupsWidth respeita gap e modo", () => {
    const list = groups([
      ["a", 100, 50],
      ["b", 100, 50],
    ]);
    expect(sumRibbonGroupsWidth(list, new Set(), 10)).toBe(210);
    expect(sumRibbonGroupsWidth(list, new Set(["b"]), 10)).toBe(160);
  });
});
