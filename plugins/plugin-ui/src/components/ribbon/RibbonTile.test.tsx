import { Circle } from "lucide-react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { RibbonTile, RibbonTiles } from "./RibbonTile";

describe("RibbonTile", () => {
  it("renderiza ícone+rótulo e dispara onClick", () => {
    const onClick = vi.fn();
    render(<RibbonTile icon={Circle} label="Início" onClick={onClick} />);
    const btn = screen.getByRole("button", { name: "Início" });
    expect(btn.className).toContain("delpi-ui-ribbon-tile");
    fireEvent.click(btn);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("RibbonTiles aplica grid compact", () => {
    const { container } = render(
      <RibbonTiles compact aria-label="Paleta">
        <RibbonTile icon={Circle} label="A" />
      </RibbonTiles>,
    );
    const root = container.querySelector(".delpi-ui-ribbon-tiles");
    expect(root?.className).toContain("delpi-ui-ribbon-tiles--compact");
  });
});
