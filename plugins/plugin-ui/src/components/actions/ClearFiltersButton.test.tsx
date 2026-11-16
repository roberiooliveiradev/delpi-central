import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ClearFiltersButton } from "./ClearFiltersButton";

afterEach(() => {
  cleanup();
});

describe("ClearFiltersButton", () => {
  it("renderiza com destaque canônico e dispara onClick", () => {
    const onClick = vi.fn();
    render(<ClearFiltersButton onClick={onClick} />);

    const button = screen.getByRole("button", { name: "Limpar filtros" });
    expect(button.className).toContain("delpi-ui-action-btn");
    expect(button.className).toContain("delpi-ui-clear-filters-btn");
    expect(button.className).not.toContain("delpi-ui-action-btn--ghost");
    fireEvent.click(button);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("aceita label customizado e densidade compacta", () => {
    render(
      <ClearFiltersButton
        onClick={() => undefined}
        label="Limpar busca e filtros"
        density="compact"
      />,
    );

    const button = screen.getByRole("button", { name: "Limpar busca e filtros" });
    expect(button.className).toContain("delpi-ui-clear-filters-btn--compact");
    expect(button.textContent).toContain("Limpar busca e filtros");
  });

  it('variant="icon" — quadrado âmbar só-ícone com FilterX e aria-label', () => {
    const onClick = vi.fn();
    render(<ClearFiltersButton variant="icon" onClick={onClick} />);

    const button = screen.getByRole("button", { name: "Limpar filtros" });
    expect(button.className).toContain("delpi-ui-icon-btn");
    expect(button.className).toContain("delpi-ui-icon-btn--amber");
    expect(button.textContent).not.toContain("Limpar filtros");
    expect(button.querySelector("svg")).toBeTruthy();
    fireEvent.click(button);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('variant="icon" respeita disabled e aria-label customizado', () => {
    const onClick = vi.fn();
    render(
      <ClearFiltersButton
        variant="icon"
        onClick={onClick}
        disabled
        aria-label="Limpar filtros da lista"
      />,
    );

    const button = screen.getByRole("button", {
      name: "Limpar filtros da lista",
    }) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    fireEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
  });
});
