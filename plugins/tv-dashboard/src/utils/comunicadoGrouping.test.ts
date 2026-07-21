import { describe, expect, it } from "vitest";
import { createBlock } from "@delpi/tv-dashboard-presentation";

import {
  expandSelectionWithGroups,
  groupBlocks,
  isIsolatedGroupChildSelection,
  resolveClosedGroupSelection,
  selectedHasGroup,
  ungroupBlocks,
  unionFramePercent,
} from "./comunicadoGrouping";

describe("comunicadoGrouping", () => {
  it("expande seleção para todos do mesmo grupo", () => {
    const a = createBlock("text", "A");
    const b = createBlock("text", "B");
    a.groupId = "grp_1";
    b.groupId = "grp_1";
    const expanded = expandSelectionWithGroups([a, b], [a.id]);
    expect(expanded.sort()).toEqual([a.id, b.id].sort());
  });

  it("agrupa e desagrupa blocos selecionados", () => {
    const a = createBlock("text", "A");
    const b = createBlock("text", "B");
    const grouped = groupBlocks([a, b], [a.id, b.id], "grp_test");
    expect(grouped.every((block) => block.groupId === "grp_test")).toBe(true);
    expect(selectedHasGroup(grouped, [a.id])).toBe(true);
    const ungrouped = ungroupBlocks(grouped, [a.id, b.id]);
    expect(ungrouped.every((block) => !block.groupId)).toBe(true);
  });

  it("detecta seleção pai fechada do grupo", () => {
    const a = createBlock("text", "A");
    const b = createBlock("text", "B");
    const c = createBlock("text", "C");
    a.groupId = "grp_1";
    b.groupId = "grp_1";
    a.frame = { x: 10, y: 10, w: 20, h: 10 };
    b.frame = { x: 15, y: 25, w: 20, h: 10 };
    const closed = resolveClosedGroupSelection([a, b, c], [a.id, b.id]);
    expect(closed?.groupId).toBe("grp_1");
    expect(closed?.memberIds.sort()).toEqual([a.id, b.id].sort());
    expect(resolveClosedGroupSelection([a, b, c], [a.id])).toBeNull();
    expect(isIsolatedGroupChildSelection([a, b], [a.id])).toBe(true);
    expect(isIsolatedGroupChildSelection([a, b], [a.id, b.id])).toBe(false);
  });

  it("une frames percentuais do grupo", () => {
    expect(
      unionFramePercent([
        { x: 10, y: 10, w: 20, h: 10 },
        { x: 15, y: 25, w: 20, h: 10 },
      ]),
    ).toEqual({ x: 10, y: 10, w: 25, h: 25 });
  });
});
