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
});
