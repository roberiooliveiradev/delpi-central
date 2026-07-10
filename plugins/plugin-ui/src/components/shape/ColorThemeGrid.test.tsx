import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ColorThemeGrid } from "./ColorThemeGrid";
import { DELPI_THEME_COLOR_GRID } from "./colorPalettes";

describe("ColorThemeGrid", () => {
  it("renderiza grade de cores do tema", () => {
    render(
      <ColorThemeGrid
        rows={DELPI_THEME_COLOR_GRID}
        value="#089bdb"
        onSelect={vi.fn()}
        ariaLabel="Cores do Tema"
      />,
    );

    expect(screen.getByRole("grid", { name: "Cores do Tema" })).toBeTruthy();
  });
});
