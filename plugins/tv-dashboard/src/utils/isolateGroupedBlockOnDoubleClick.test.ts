import { describe, expect, it, vi } from "vitest";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import { isolateGroupedBlockOnDoubleClick } from "./isolateGroupedBlockOnDoubleClick";

function fakeIcon(id: string, groupId?: string): ComunicadoBlock {
  return {
    id,
    type: "icon",
    iconName: "Target",
    frame: { x: 10, y: 10, w: 20, h: 10 },
    ...(groupId ? { groupId } : {}),
  };
}

function fakeText(id: string, groupId?: string): ComunicadoBlock {
  return {
    id,
    type: "text",
    content: id,
    frame: { x: 10, y: 10, w: 20, h: 10 },
    ...(groupId ? { groupId } : {}),
  };
}

describe("isolateGroupedBlockOnDoubleClick", () => {
  it("isola ícone quando o grupo fechado está selecionado", () => {
    const a = fakeIcon("a", "grp");
    const b = fakeIcon("b", "grp");
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

  it("isola ícone mesmo se o grupo ainda não estiver selecionado", () => {
    const a = fakeIcon("a", "grp");
    const b = fakeIcon("b", "grp");
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
    const a = fakeIcon("a");
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

  it("texto em grupo não isola aqui — policy devolve enter-text-edit", () => {
    const a = fakeText("a", "grp");
    const b = fakeText("b", "grp");
    const selectBlock = vi.fn();
    expect(
      isolateGroupedBlockOnDoubleClick({
        block: a,
        blocks: [a, b],
        selectedIds: ["a", "b"],
        selectBlock,
      }),
    ).toBe(false);
    expect(selectBlock).not.toHaveBeenCalled();
  });
});
