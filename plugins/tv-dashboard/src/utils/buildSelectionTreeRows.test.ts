import { describe, expect, it } from "vitest";
import { createBlock } from "@delpi/tv-dashboard-presentation";

import {
  buildSelectionTreeRows,
  selectionTreeRowIsActive,
} from "./buildSelectionTreeRows";

describe("buildSelectionTreeRows", () => {
  it("aninha membros sob o nó do grupo e mantém soltos na raiz", () => {
    const a = createBlock("text", "A");
    const b = createBlock("text", "B");
    const c = createBlock("text", "C");
    a.groupId = "g1";
    b.groupId = "g1";
    a.style = { ...a.style, zIndex: 3 };
    b.style = { ...b.style, zIndex: 2 };
    c.style = { ...c.style, zIndex: 1 };

    const rows = buildSelectionTreeRows([a, b, c]);
    expect(rows.map((row) => row.kind)).toEqual(["group", "block", "block", "block"]);
    expect(rows[0]).toMatchObject({ kind: "group", groupId: "g1", memberIds: [a.id, b.id] });
    expect(rows[1]).toMatchObject({ kind: "block", depth: 1, block: expect.objectContaining({ id: a.id }) });
    expect(rows[2]).toMatchObject({ kind: "block", depth: 1, block: expect.objectContaining({ id: b.id }) });
    expect(rows[3]).toMatchObject({ kind: "block", depth: 0, block: expect.objectContaining({ id: c.id }) });
  });

  it("marca grupo ativo só com todos os membros selecionados", () => {
    const a = createBlock("text", "A");
    const b = createBlock("text", "B");
    a.groupId = "g1";
    b.groupId = "g1";
    const rows = buildSelectionTreeRows([a, b]);
    const group = rows[0]!;
    expect(selectionTreeRowIsActive(group, [a.id, b.id])).toBe(true);
    expect(selectionTreeRowIsActive(group, [a.id])).toBe(false);
  });
});
