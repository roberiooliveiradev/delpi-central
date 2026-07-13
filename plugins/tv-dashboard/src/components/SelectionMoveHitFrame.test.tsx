import { cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import { SelectionMoveHitFrame } from "./SelectionMoveHitFrame";

afterEach(() => {
  cleanup();
});

const block = {
  id: "blk-1",
  type: "chart_view",
  frame: { x: 10, y: 10, w: 40, h: 40 },
  chartType: "bar",
} as ComunicadoBlock;

describe("SelectionMoveHitFrame", () => {
  it("expõe as quatro bordas de arraste alinhadas ao outline", () => {
    const { container } = render(<SelectionMoveHitFrame block={block} onMovePointerDown={vi.fn()} />);
    expect(container.querySelector(".td-composer__selection-move-edge--n")).toBeTruthy();
    expect(container.querySelector(".td-composer__selection-move-edge--e")).toBeTruthy();
    expect(container.querySelector(".td-composer__selection-move-edge--s")).toBeTruthy();
    expect(container.querySelector(".td-composer__selection-move-edge--w")).toBeTruthy();
  });

  it("dispara move no pointerdown de qualquer borda", () => {
    const onMove = vi.fn();
    const { container } = render(<SelectionMoveHitFrame block={block} onMovePointerDown={onMove} />);
    const edge = container.querySelector(".td-composer__selection-move-edge--n");
    expect(edge).toBeTruthy();
    fireEvent.pointerDown(edge!);
    expect(onMove).toHaveBeenCalledTimes(1);
    expect(onMove.mock.calls[0][1]).toBe(block);
    expect(onMove.mock.calls[0][2]).toBe("move");
  });

  it("não usa button (evita hover global do portal)", () => {
    const { container } = render(<SelectionMoveHitFrame block={block} onMovePointerDown={vi.fn()} />);
    expect(container.querySelector("button")).toBeNull();
    expect(container.querySelectorAll(".td-composer__selection-move-edge")).toHaveLength(4);
  });
});
