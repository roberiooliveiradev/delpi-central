import { describe, expect, it } from "vitest";
import { createBlock } from "@delpi/tv-dashboard-presentation";

import {
  expandSelectionWithGroups,
  groupBlocks,
  selectedHasGroup,
  ungroupBlocks,
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
});
