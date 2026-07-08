import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { FilterBarShell, filterBarShellBemClasses } from "./FilterBarShell";

describe("FilterBarShell", () => {
  it("renderiza form com card quando não embedded", () => {
    render(
      <FilterBarShell
        onSubmit={vi.fn()}
        classNames={filterBarShellBemClasses("dm")}
        ariaLabel="Filtros"
      >
        <input aria-label="Busca" />
      </FilterBarShell>,
    );

    const form = screen.getByRole("form", { name: "Filtros" });
    expect(form.className).toContain("dm-card");
    expect(form.className).toContain("dm-filter-bar");
  });

  it("layout grid envolve filhos em __grid", () => {
    render(
      <FilterBarShell
        layout="grid"
        classNames={filterBarShellBemClasses("ef", { withGrid: true })}
      >
        <span>Filtro</span>
      </FilterBarShell>,
    );

    expect(document.querySelector(".ef-filter-bar__grid")).toBeTruthy();
  });

  it("suporta block BEM customizado (analytics-filters)", () => {
    render(
      <FilterBarShell
        layout="grid"
        embedded
        classNames={filterBarShellBemClasses("a5s", {
          withGrid: true,
          block: "analytics-filters",
        })}
        ariaLabel="Filtros do painel"
      >
        <span>Campo</span>
      </FilterBarShell>,
    );

    const section = screen.getByRole("region", { name: "Filtros do painel" });
    expect(section.className).toContain("a5s-analytics-filters");
    expect(section.className).not.toContain("a5s-card");
    expect(document.querySelector(".a5s-analytics-filters__grid")).toBeTruthy();
  });
});
