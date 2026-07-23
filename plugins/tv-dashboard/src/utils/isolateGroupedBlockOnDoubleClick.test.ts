import { describe, expect, it, vi } from "vitest";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import { isolateGroupedBlockOnDoubleClick } from "./isolateGroupedBlockOnDoubleClick";

function fakeBlock(id: string, groupId?: string): ComunicadoBlock {
  return {
    id,
    type: "text",
    content: id,
    frame: { x: 10, y: 10, w: 20, h: 10 },
    ...(groupId ? { groupId } : {}),
  };
}

describe("isolateGroupedBlockOnDoubleClick", () => {
  it("isola membro quando o grupo fechado está selecionado", () => {
    const a = fakeBlock("a", "grp");
    const b = fakeBlock("b", "grp");
    const selectBlock = vi.fn();
    expect(
      isolateGroupedBlockOnDoubleClick({
        block: a,
        blocks: [a, b],
        selectedIds: ["a", "b"],
        selectBlock,
      }),
    ).toBe(true);
    expect(selectBlock).toHaveBeenCalledWith("a", { expandGroup: false });
  });

  it("isola mesmo se o grupo ainda não estiver selecionado", () => {
    const a = fakeBlock("a", "grp");
    const b = fakeBlock("b", "grp");
    const selectBlock = vi.fn();
    expect(
      isolateGroupedBlockOnDoubleClick({
        block: a,
        blocks: [a, b],
        selectedIds: [],
        selectBlock,
      }),
    ).toBe(true);
    expect(selectBlock).toHaveBeenCalledWith("a", { expandGroup: false });
  });

  it("ignora bloco sem grupo", () => {
    const a = fakeBlock("a");
    const selectBlock = vi.fn();
    expect(
      isolateGroupedBlockOnDoubleClick({
        block: a,
        blocks: [a],
        selectedIds: ["a"],
        selectBlock,
      }),
    ).toBe(false);
    expect(selectBlock).not.toHaveBeenCalled();
  });
});
