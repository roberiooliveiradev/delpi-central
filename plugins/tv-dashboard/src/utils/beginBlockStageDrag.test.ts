import { describe, expect, it, vi } from "vitest";
import type { PointerEvent as ReactPointerEvent } from "react";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import { beginBlockStageMoveDrag } from "./beginBlockStageDrag";

function fakeBlock(id: string, groupId?: string): ComunicadoBlock {
  return {
    id,
    type: "text",
    content: id,
    frame: { x: 10, y: 10, w: 20, h: 10 },
    ...(groupId ? { groupId } : {}),
  };
}

function fakeEvent(partial: Partial<ReactPointerEvent> = {}): ReactPointerEvent {
  return {
    shiftKey: false,
    ctrlKey: false,
    metaKey: false,
    ...partial,
  } as ReactPointerEvent;
}

describe("beginBlockStageMoveDrag", () => {
  it("Ctrl+clique isola filho do grupo sem iniciar drag", () => {
    const a = fakeBlock("a", "grp");
    const b = fakeBlock("b", "grp");
    const selectBlock = vi.fn();
    const startDrag = vi.fn();
    const result = beginBlockStageMoveDrag({
      event: fakeEvent({ ctrlKey: true }),
      block: a,
      blocks: [a, b],
      isBlockSelected: () => false,
      selectedIds: [],
      selectedId: null,
      selectBlock,
      selectBlocksByIds: vi.fn(),
      armMultiDragSelection: vi.fn(),
      startDrag,
    });
    expect(result).toBe(false);
    expect(selectBlock).toHaveBeenCalledWith("a", { expandGroup: false });
    expect(startDrag).not.toHaveBeenCalled();
  });

  it("2º clique com seleção pai isola o membro e inicia drag só dele", () => {
    const a = fakeBlock("a", "grp");
    const b = fakeBlock("b", "grp");
    const selectBlock = vi.fn();
    const armMultiDragSelection = vi.fn();
    const startDrag = vi.fn();
    const result = beginBlockStageMoveDrag({
      event: fakeEvent(),
      block: a,
      blocks: [a, b],
      isBlockSelected: (id) => id === "a" || id === "b",
      selectedIds: ["a", "b"],
      selectedId: "a",
      selectBlock,
      selectBlocksByIds: vi.fn(),
      armMultiDragSelection,
      startDrag,
    });
    expect(result).toBe(true);
    expect(selectBlock).toHaveBeenCalledWith("a", { expandGroup: false });
    expect(armMultiDragSelection).toHaveBeenCalledWith(["a"]);
    expect(startDrag).toHaveBeenCalled();
  });

  it("1º clique em membro seleciona o grupo e arrasta juntos", () => {
    const a = fakeBlock("a", "grp");
    const b = fakeBlock("b", "grp");
    const selectBlock = vi.fn();
    const armMultiDragSelection = vi.fn();
    const startDrag = vi.fn();
    const result = beginBlockStageMoveDrag({
      event: fakeEvent(),
      block: a,
      blocks: [a, b],
      isBlockSelected: () => false,
      selectedIds: [],
      selectedId: null,
      selectBlock,
      selectBlocksByIds: vi.fn(),
      armMultiDragSelection,
      startDrag,
    });
    expect(result).toBe(true);
    expect(selectBlock).toHaveBeenCalledWith("a");
    expect(armMultiDragSelection).toHaveBeenCalledWith(["a", "b"]);
    expect(startDrag).toHaveBeenCalled();
  });
});
