// @vitest-environment jsdom

import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { DragEvent } from "react";

import {
  dragAutoScrollDelta,
  moveArrayItems,
  resolveScrollParent,
  useMachineLoadRowReorder,
} from "./useMachineLoadRowReorder";

const dragEvent = (index = 0): DragEvent =>
  ({
    dataTransfer: {
      effectAllowed: "",
      dropEffect: "",
      setData: vi.fn(),
      getData: () => String(index),
    },
    currentTarget: document.createElement("button"),
    preventDefault: vi.fn(),
  }) as unknown as DragEvent;

describe("moveArrayItems", () => {
  it("equivale a moveArrayItem para um único índice", () => {
    expect(moveArrayItems(["a", "b", "c"], [0], 2)).toEqual(["b", "c", "a"]);
    expect(moveArrayItems(["a", "b", "c"], [2], 0)).toEqual(["c", "a", "b"]);
  });

  it("move bloco preservando a ordem relativa — cabeça no índice do alvo", () => {
    expect(moveArrayItems(["a", "b", "c", "d", "e"], [1, 3], 4)).toEqual([
      "a",
      "c",
      "e",
      "b",
      "d",
    ]);
  });

  it("move bloco para trás do alvo", () => {
    expect(moveArrayItems(["a", "b", "c", "d", "e"], [2, 4], 1)).toEqual([
      "a",
      "c",
      "e",
      "b",
      "d",
    ]);
  });

  it("conjunto vazio retorna a lista original", () => {
    const items = ["a", "b"];
    expect(moveArrayItems(items, [], 1)).toBe(items);
  });
});

describe("resolveScrollParent", () => {
  it("elemento destacado cai no scroll do documento", () => {
    const detached = document.createElement("button");
    expect(resolveScrollParent(detached)).toBe(
      document.scrollingElement ?? document.documentElement,
    );
  });

  it("encontra ancestral com overflow-y e conteúdo excedente", () => {
    const outer = document.createElement("div");
    const inner = document.createElement("div");
    outer.style.overflowY = "auto";
    Object.defineProperty(outer, "scrollHeight", { value: 500 });
    Object.defineProperty(outer, "clientHeight", { value: 200 });
    outer.appendChild(inner);
    document.body.appendChild(outer);
    expect(resolveScrollParent(inner)).toBe(outer);
    document.body.removeChild(outer);
  });
});

describe("dragAutoScrollDelta", () => {
  it("documento: negativo no topo, positivo no rodapé, zero no meio", () => {
    const el = document.documentElement;
    const height = window.innerHeight;
    expect(dragAutoScrollDelta(el, 0)).toBeLessThan(0);
    expect(dragAutoScrollDelta(el, height - 5)).toBeGreaterThan(0);
    expect(dragAutoScrollDelta(el, height / 2)).toBe(0);
  });

  it("velocidade máxima na borda e proporcional perto dela", () => {
    const el = document.documentElement;
    const atEdge = Math.abs(dragAutoScrollDelta(el, 0));
    const nearEdge = Math.abs(dragAutoScrollDelta(el, 30));
    expect(atEdge).toBeGreaterThan(nearEdge);
    expect(atEdge).toBeLessThanOrEqual(16);
  });
});

describe("useMachineLoadRowReorder", () => {
  it("drop individual reordena a linha", () => {
    const onReorder = vi.fn();
    const { result } = renderHook(() =>
      useMachineLoadRowReorder(["a", "b", "c"], onReorder),
    );
    act(() => result.current.handleProps(0).onDragStart(dragEvent()));
    act(() => result.current.rowDropProps(2).onDrop(dragEvent()));
    expect(onReorder).toHaveBeenCalledWith(["b", "c", "a"]);
  });

  it("com seleção, só linhas selecionadas têm handle arrastável", () => {
    const onReorder = vi.fn();
    const { result } = renderHook(() =>
      useMachineLoadRowReorder(["a", "b", "c", "d"], onReorder, {
        selectedIndices: new Set([1, 3]),
      }),
    );
    expect(result.current.handleProps(0).draggable).toBe(false);
    expect(result.current.handleProps(1).draggable).toBe(true);
    expect(result.current.handleProps(3).draggable).toBe(true);
  });

  it("drop de grupo move o bloco e chama o veto antes", () => {
    const onReorder = vi.fn();
    const veto = vi.fn().mockReturnValue(true);
    const { result } = renderHook(() =>
      useMachineLoadRowReorder(["a", "b", "c", "d", "e"], onReorder, {
        selectedIndices: new Set([1, 3]),
        onBeforeGroupDrop: veto,
      }),
    );
    act(() => result.current.handleProps(3).onDragStart(dragEvent()));
    expect(result.current.draggedIndices).toEqual([1, 3]);
    act(() => result.current.rowDropProps(4).onDrop(dragEvent()));
    expect(veto).toHaveBeenCalledWith([1, 3], 4);
    expect(onReorder).toHaveBeenCalledWith(["a", "c", "e", "b", "d"]);
  });

  it("veto negado aborta o drop — nada é reordenado", () => {
    const onReorder = vi.fn();
    const veto = vi.fn().mockReturnValue(false);
    const { result } = renderHook(() =>
      useMachineLoadRowReorder(["a", "b", "c"], onReorder, {
        selectedIndices: new Set([0, 2]),
        onBeforeGroupDrop: veto,
      }),
    );
    act(() => result.current.handleProps(0).onDragStart(dragEvent()));
    act(() => result.current.rowDropProps(1).onDrop(dragEvent()));
    expect(veto).toHaveBeenCalledWith([0, 2], 1);
    expect(onReorder).not.toHaveBeenCalled();
  });

  it("drop sobre linha do próprio grupo não faz nada", () => {
    const onReorder = vi.fn();
    const veto = vi.fn().mockReturnValue(true);
    const { result } = renderHook(() =>
      useMachineLoadRowReorder(["a", "b", "c"], onReorder, {
        selectedIndices: new Set([0, 2]),
        onBeforeGroupDrop: veto,
      }),
    );
    act(() => result.current.handleProps(0).onDragStart(dragEvent()));
    act(() => result.current.rowDropProps(2).onDrop(dragEvent()));
    expect(veto).not.toHaveBeenCalled();
    expect(onReorder).not.toHaveBeenCalled();
  });

  it("enabled=false ignora dragover/drop", () => {
    const onReorder = vi.fn();
    const { result } = renderHook(() =>
      useMachineLoadRowReorder(["a", "b"], onReorder, { enabled: false }),
    );
    act(() => result.current.rowDropProps(1).onDrop(dragEvent()));
    expect(onReorder).not.toHaveBeenCalled();
  });
});
