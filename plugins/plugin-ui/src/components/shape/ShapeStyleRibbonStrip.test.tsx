import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  SHAPE_THEME_STYLE_PRESETS,
  ShapeStyleRibbonStrip,
} from "./ShapeStyleGallery";

describe("ShapeStyleRibbonStrip", () => {
  it("mostra thumbs Abc e aplica preset ao clicar", () => {
    const onSelect = vi.fn();
    render(
      <ShapeStyleRibbonStrip
        maxVisible={3}
        themePresets={SHAPE_THEME_STYLE_PRESETS.slice(0, 3)}
        onSelect={onSelect}
      />,
    );
    const thumbs = screen.getAllByRole("listitem");
    expect(thumbs.length).toBeGreaterThanOrEqual(3);
    fireEvent.click(thumbs[1]!);
    expect(onSelect).toHaveBeenCalledWith(
      expect.objectContaining({ id: SHAPE_THEME_STYLE_PRESETS[1]!.id }),
    );
    expect(screen.getByText("Mais")).toBeTruthy();
  });
});
