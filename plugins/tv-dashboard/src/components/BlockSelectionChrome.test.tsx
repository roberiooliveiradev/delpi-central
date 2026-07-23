import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  createIconBlock,
  createKpiViewBlock,
  createShapeBlock,
} from "@delpi/tv-dashboard-presentation";

import { BlockSelectionChrome } from "./BlockSelectionChrome";

describe("BlockSelectionChrome", () => {
  it("expõe os mesmos controles de seleção para ícone e forma", () => {
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
        block={createShapeBlock("rectangle")}
        designShortSidePx={64}
        allowResize
        onPointerDown={onPointerDown}
      />,
    );
    expect(screen.getByLabelText("Girar elemento")).toBeTruthy();
    expect(screen.getByLabelText(/canto superior esquerdo/i)).toBeTruthy();
    expect(screen.getByLabelText(/Ajustar/i)).toBeTruthy();
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
