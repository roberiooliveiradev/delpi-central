import { describe, expect, it } from "vitest";
import { createBlock } from "@delpi/tv-dashboard-presentation";

import {
  expandSelectionWithGroups,
  groupBlocks,
  isIsolatedGroupChildSelection,
  partitionSelectionIntoLayoutUnits,
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

  it("particiona dois grupos fechados em duas unidades de layout", () => {
    const a = createBlock("text", "A");
    const b = createBlock("text", "B");
    const c = createBlock("text", "C");
    const d = createBlock("text", "D");
    a.groupId = "g1";
    b.groupId = "g1";
    c.groupId = "g2";
    d.groupId = "g2";
    a.frame = { x: 0, y: 0, w: 10, h: 10 };
    b.frame = { x: 10, y: 10, w: 10, h: 10 };
    c.frame = { x: 40, y: 0, w: 10, h: 10 };
    d.frame = { x: 50, y: 10, w: 10, h: 10 };
    const units = partitionSelectionIntoLayoutUnits(
      [a, b, c, d],
      [a.id, b.id, c.id, d.id],
    );
    expect(units).toHaveLength(2);
    expect(units.map((unit) => unit.key).sort()).toEqual(["g1", "g2"]);
    expect(units.find((unit) => unit.key === "g1")?.frame).toEqual({ x: 0, y: 0, w: 20, h: 20 });
  });

  it("filho isolado permanece unidade própria", () => {
    const a = createBlock("text", "A");
    const b = createBlock("text", "B");
    a.groupId = "g1";
    b.groupId = "g1";
    const units = partitionSelectionIntoLayoutUnits([a, b], [a.id]);
    expect(units).toHaveLength(1);
    expect(units[0]?.key).toBe(a.id);
  });
});
