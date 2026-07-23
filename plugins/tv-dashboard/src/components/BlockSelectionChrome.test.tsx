import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  createIconBlock,
  createKpiViewBlock,
  createShapeBlock,
} from "@delpi/tv-dashboard-presentation";

import { BlockSelectionChrome } from "./BlockSelectionChrome";

afterEach(() => {
  cleanup();
});

describe("BlockSelectionChrome", () => {
  it("expõe os mesmos controles de seleção para ícone e forma com ajuste", () => {
    const onPointerDown = vi.fn();
    const { rerender } = render(
      <BlockSelectionChrome
        block={createIconBlock("Factory")}
        designShortSidePx={64}
        allowResize
        onPointerDown={onPointerDown}
      />,
    );
    expect(screen.getByLabelText("Girar elemento")).toBeTruthy();
    expect(screen.getByLabelText(/canto superior esquerdo/i)).toBeTruthy();
    expect(screen.getByLabelText(/Ajustar/i)).toBeTruthy();

    rerender(
      <BlockSelectionChrome
        block={createShapeBlock("rounded-rect")}
        designShortSidePx={64}
        allowResize
        onPointerDown={onPointerDown}
      />,
    );
    expect(screen.getByLabelText("Girar elemento")).toBeTruthy();
    expect(screen.getByLabelText(/canto superior esquerdo/i)).toBeTruthy();
    expect(screen.getByLabelText(/Ajustar/i)).toBeTruthy();
  });

  it("linha: só endpoints + giro — sem 8 handles de bbox", () => {
    const onPointerDown = vi.fn();
    const line = {
      ...createShapeBlock("line"),
      frame: { x: 10, y: 20, w: 30, h: 2 },
      vertices: [
        { x: 10, y: 21 },
        { x: 40, y: 21 },
      ],
    };
    render(
      <BlockSelectionChrome
        block={line}
        designShortSidePx={20}
        allowResize={false}
        onPointerDown={onPointerDown}
      />,
    );
    expect(screen.getByLabelText("Girar elemento")).toBeTruthy();
    expect(screen.getByLabelText("Mover início da linha")).toBeTruthy();
    expect(screen.getByLabelText("Mover fim da linha")).toBeTruthy();
    expect(screen.queryByLabelText(/canto superior esquerdo/i)).toBeNull();
    expect(screen.queryByLabelText(/Redimensionar borda/i)).toBeNull();
  });

  it("retângulo puro: sem losango de adjustment (paridade PPT)", () => {
    const onPointerDown = vi.fn();
    render(
      <BlockSelectionChrome
        block={createShapeBlock("rectangle")}
        designShortSidePx={64}
        allowResize
        onPointerDown={onPointerDown}
      />,
    );
    expect(screen.getByLabelText(/canto superior esquerdo/i)).toBeTruthy();
    expect(screen.queryByLabelText(/Ajustar/i)).toBeNull();
  });

  it("expõe losango de ajuste também no KPI (cantos do card)", () => {
    const onPointerDown = vi.fn();
    render(
      <BlockSelectionChrome
        block={createKpiViewBlock()}
        designShortSidePx={64}
        allowResize
        onPointerDown={onPointerDown}
      />,
    );
    expect(screen.getAllByLabelText("Ajustar Cantos").length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByLabelText("Redimensionar canto superior esquerdo").length,
    ).toBeGreaterThanOrEqual(1);
  });
});
