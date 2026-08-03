import { render, screen, within } from "@testing-library/react";
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

  it("transparent não marca o swatch preto do tema", () => {
    const { container } = render(
      <ColorThemeGrid
        rows={DELPI_THEME_COLOR_GRID}
        value="transparent"
        onSelect={vi.fn()}
        ariaLabel="Cores do Tema"
      />,
    );
    const grid = within(container);
    const selected = grid.queryAllByRole("button", { pressed: true });
    expect(selected).toHaveLength(0);
  });

  it("auto não marca o swatch preto do tema", () => {
    const { container } = render(
      <ColorThemeGrid
        rows={DELPI_THEME_COLOR_GRID}
        value="auto"
        onSelect={vi.fn()}
        ariaLabel="Cores do Tema"
      />,
    );
    expect(within(container).queryAllByRole("button", { pressed: true })).toHaveLength(0);
  });

  it("marca a cor explícita selecionada", () => {
    const { container } = render(
      <ColorThemeGrid
        rows={DELPI_THEME_COLOR_GRID}
        value="#000000"
        onSelect={vi.fn()}
        ariaLabel="Cores do Tema"
      />,
    );
    const selected = within(container).getAllByRole("button", { pressed: true });
    expect(selected.length).toBeGreaterThanOrEqual(1);
    expect(selected[0]?.getAttribute("aria-label")?.toLowerCase()).toBe("#000000");
  });
});
