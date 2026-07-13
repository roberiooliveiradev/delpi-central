import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SelectionMoveHitFrame } from "./SelectionMoveHitFrame";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

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
    render(<SelectionMoveHitFrame block={block} onMovePointerDown={vi.fn()} />);
    expect(screen.getByLabelText("Mover pela borda superior")).toBeTruthy();
    expect(screen.getByLabelText("Mover pela borda direita")).toBeTruthy();
    expect(screen.getByLabelText("Mover pela borda inferior")).toBeTruthy();
    expect(screen.getByLabelText("Mover pela borda esquerda")).toBeTruthy();
  });

  it("dispara move no pointerdown de qualquer borda", () => {
    const onMove = vi.fn();
    render(<SelectionMoveHitFrame block={block} onMovePointerDown={onMove} />);
    fireEvent.pointerDown(screen.getByLabelText("Mover pela borda superior"));
    expect(onMove).toHaveBeenCalledTimes(1);
    expect(onMove.mock.calls[0][1]).toBe(block);
    expect(onMove.mock.calls[0][2]).toBe("move");
  });
});
