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
    button: 0,
    shiftKey: false,
    ctrlKey: false,
    metaKey: false,
    altKey: false,
    ...partial,
  } as ReactPointerEvent;
}

describe("beginBlockStageMoveDrag", () => {
  it("botão direito não seleciona nem inicia drag", () => {
    const a = fakeBlock("a");
    const selectBlock = vi.fn();
    const startDrag = vi.fn();
    const result = beginBlockStageMoveDrag({
      event: fakeEvent({ button: 2 }),
      block: a,
      blocks: [a],
      isBlockSelected: () => false,
      selectedIds: [],
      selectedId: null,
      selectBlock,
      selectBlocksByIds: vi.fn(),
      armMultiDragSelection: vi.fn(),
      startDrag,
    });
    expect(result).toBe(false);
    expect(selectBlock).not.toHaveBeenCalled();
    expect(startDrag).not.toHaveBeenCalled();
  });

  it("Ctrl+clique no membro do grupo fechado alterna o filho sem iniciar drag", () => {
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
    /* Mesmo grupo na seleção: Ctrl alterna o membro (não subtract do grupo inteiro). */
    expect(selectBlock).toHaveBeenCalledWith("a", { additive: true, expandGroup: false });
    expect(startDrag).not.toHaveBeenCalled();
    expect(armTapDeselect).toHaveBeenCalledWith(null);
  });

  it("Ctrl+clique fora do grupo remove da seleção", () => {
    const a = fakeBlock("a", "grp");
    const x = fakeBlock("x");
    const selectBlock = vi.fn();
    const result = beginBlockStageMoveDrag({
      event: fakeEvent({ ctrlKey: true }),
      block: x,
      blocks: [a, x],
      isBlockSelected: () => true,
      selectedIds: ["a", "x"],
      selectedId: "x",
      selectBlock,
      selectBlocksByIds: vi.fn(),
      armMultiDragSelection: vi.fn(),
      startDrag: vi.fn(),
      armTapDeselect: vi.fn(),
    });
    expect(result).toBe(false);
    expect(selectBlock).toHaveBeenCalledWith("x", { subtract: true, expandGroup: false });
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

  it("Shift com grupo selecionado alterna o membro (não desliga o grupo inteiro)", () => {
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
    expect(selectBlock).toHaveBeenCalledWith("a", { additive: true, expandGroup: false });
    expect(startDrag).not.toHaveBeenCalled();
  });

  it("Ctrl em irmão do mesmo grupo adiciona o membro à seleção", () => {
    const a = fakeBlock("a", "grp");
    const b = fakeBlock("b", "grp");
    const selectBlock = vi.fn();
    const result = beginBlockStageMoveDrag({
      event: fakeEvent({ ctrlKey: true }),
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

  it("texto já isolado não arma tap-deselect (protege dblclick → editar)", () => {
    const a = fakeBlock("a", "grp");
    const b = fakeBlock("b", "grp");
    const armTapDeselect = vi.fn();
    beginBlockStageMoveDrag({
      event: fakeEvent(),
      block: a,
      blocks: [a, b],
      isBlockSelected: (id) => id === "a",
      selectedIds: ["a"],
      selectedId: "a",
      selectBlock: vi.fn(),
      selectBlocksByIds: vi.fn(),
      armMultiDragSelection: vi.fn(),
      startDrag: vi.fn(),
      armTapDeselect,
    });
    expect(armTapDeselect).toHaveBeenCalledWith(null);
  });

  it("ícone já isolado arma tap-deselect", () => {
    const a: ComunicadoBlock = {
      id: "a",
      type: "icon",
      iconName: "Target",
      frame: { x: 10, y: 10, w: 20, h: 10 },
      groupId: "grp",
    };
    const b: ComunicadoBlock = {
      id: "b",
      type: "icon",
      iconName: "Star",
      frame: { x: 30, y: 10, w: 20, h: 10 },
      groupId: "grp",
    };
    const armTapDeselect = vi.fn();
    beginBlockStageMoveDrag({
      event: fakeEvent(),
      block: a,
      blocks: [a, b],
      isBlockSelected: (id) => id === "a",
      selectedIds: ["a"],
      selectedId: "a",
      selectBlock: vi.fn(),
      selectBlocksByIds: vi.fn(),
      armMultiDragSelection: vi.fn(),
      startDrag: vi.fn(),
      armTapDeselect,
    });
    expect(armTapDeselect).toHaveBeenCalledWith("a");
  });
});
