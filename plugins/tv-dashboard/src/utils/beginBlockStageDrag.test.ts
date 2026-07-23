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
    altKey: false,
    ...partial,
  } as ReactPointerEvent;
}

describe("beginBlockStageMoveDrag", () => {
  it("Ctrl+clique remove da seleção sem iniciar drag", () => {
    const a = fakeBlock("a", "grp");
    const b = fakeBlock("b", "grp");
    const selectBlock = vi.fn();
    const startDrag = vi.fn();
    const armTapDeselect = vi.fn();
    const result = beginBlockStageMoveDrag({
      event: fakeEvent({ ctrlKey: true }),
      block: a,
      blocks: [a, b],
      isBlockSelected: () => true,
      selectedIds: ["a", "b"],
      selectedId: "a",
      selectBlock,
      selectBlocksByIds: vi.fn(),
      armMultiDragSelection: vi.fn(),
      startDrag,
      armTapDeselect,
    });
    expect(result).toBe(false);
    expect(selectBlock).toHaveBeenCalledWith("a", { subtract: true, expandGroup: false });
    expect(startDrag).not.toHaveBeenCalled();
    expect(armTapDeselect).toHaveBeenCalledWith(null);
  });

  it("2º clique com o grupo selecionado isola o subitem", () => {
    const a = fakeBlock("a", "grp");
    const b = fakeBlock("b", "grp");
    const selectBlock = vi.fn();
    const armMultiDragSelection = vi.fn();
    const startDrag = vi.fn();
    const armTapDeselect = vi.fn();
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
      armTapDeselect,
    });
    expect(result).toBe(true);
    expect(selectBlock).toHaveBeenCalledWith("a", { expandGroup: false });
    expect(armTapDeselect).toHaveBeenCalledWith(null);
    expect(armMultiDragSelection).toHaveBeenCalledWith(["a"]);
    expect(startDrag).toHaveBeenCalled();
  });

  it("1º clique em membro seleciona o grupo e arrasta juntos", () => {
    const a = fakeBlock("a", "grp");
    const b = fakeBlock("b", "grp");
    const selectBlock = vi.fn();
    const armMultiDragSelection = vi.fn();
    const startDrag = vi.fn();
    const armTapDeselect = vi.fn();
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
      armTapDeselect,
    });
    expect(result).toBe(true);
    expect(selectBlock).toHaveBeenCalledWith("a");
    expect(armTapDeselect).toHaveBeenCalledWith(null);
    expect(armMultiDragSelection).toHaveBeenCalledWith(["a", "b"]);
    expect(startDrag).toHaveBeenCalled();
  });

  it("Shift com grupo selecionado isola o subitem para multi", () => {
    const a = fakeBlock("a", "grp");
    const b = fakeBlock("b", "grp");
    const selectBlock = vi.fn();
    const startDrag = vi.fn();
    const result = beginBlockStageMoveDrag({
      event: fakeEvent({ shiftKey: true }),
      block: a,
      blocks: [a, b],
      isBlockSelected: () => true,
      selectedIds: ["a", "b"],
      selectedId: "a",
      selectBlock,
      selectBlocksByIds: vi.fn(),
      armMultiDragSelection: vi.fn(),
      startDrag,
      armTapDeselect: vi.fn(),
    });
    expect(result).toBe(false);
    expect(selectBlock).toHaveBeenCalledWith("a", { expandGroup: false });
    expect(startDrag).not.toHaveBeenCalled();
  });

  it("Shift em modo filhos faz toggle do subitem", () => {
    const a = fakeBlock("a", "grp");
    const b = fakeBlock("b", "grp");
    const selectBlock = vi.fn();
    const result = beginBlockStageMoveDrag({
      event: fakeEvent({ shiftKey: true }),
      block: b,
      blocks: [a, b],
      isBlockSelected: (id) => id === "a",
      selectedIds: ["a"],
      selectedId: "a",
      selectBlock,
      selectBlocksByIds: vi.fn(),
      armMultiDragSelection: vi.fn(),
      startDrag: vi.fn(),
      armTapDeselect: vi.fn(),
    });
    expect(result).toBe(false);
    expect(selectBlock).toHaveBeenCalledWith("b", { additive: true, expandGroup: false });
  });

  it("Alt+clique isola o membro mesmo fora da seleção pai", () => {
    const a = fakeBlock("a", "grp");
    const b = fakeBlock("b", "grp");
    const selectBlock = vi.fn();
    const armMultiDragSelection = vi.fn();
    const startDrag = vi.fn();
    const armTapDeselect = vi.fn();
    const result = beginBlockStageMoveDrag({
      event: fakeEvent({ altKey: true }),
      block: a,
      blocks: [a, b],
      isBlockSelected: () => false,
      selectedIds: [],
      selectedId: null,
      selectBlock,
      selectBlocksByIds: vi.fn(),
      armMultiDragSelection,
      startDrag,
      armTapDeselect,
    });
    expect(result).toBe(true);
    expect(selectBlock).toHaveBeenCalledWith("a", { expandGroup: false });
    expect(armTapDeselect).toHaveBeenCalledWith(null);
    expect(armMultiDragSelection).toHaveBeenCalledWith(["a"]);
    expect(startDrag).toHaveBeenCalled();
  });
});
