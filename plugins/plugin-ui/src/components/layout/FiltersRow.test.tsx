import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FilterInputField, FiltersRow } from "./FiltersRow";

const classNames = {
  row: "dp-filters-row",
  rowExtended: "dp-filters-row dp-filters-row--extended",
  filterBox: "dp-filter-box dp-field",
  fieldLabel: "dp-field__label",
};

describe("FiltersRow", () => {
  it("renderiza section com aria-label", () => {
    render(
      <FiltersRow classNames={classNames} ariaLabel="Filtros do dashboard">
        <span>Campo</span>
      </FiltersRow>,
    );

    expect(screen.getByRole("region", { name: "Filtros do dashboard" })).toBeTruthy();
  });

  it("aplica modificador extended", () => {
    const { container } = render(
      <FiltersRow classNames={classNames} ariaLabel="Filtros" variant="extended">
        <span>Campo</span>
      </FiltersRow>,
    );

    expect(container.querySelector(".dp-filters-row--extended")).toBeTruthy();
  });

  it("suporta trailing e layout div compact", () => {
    const { container } = render(
      <FiltersRow
        as="div"
        compact
        trailing={<button type="button">Aplicar</button>}
        classNames={{
          row: "pac-filters-row",
          rowExtended: "pac-filters-row pac-filters-row--extended",
          rowCompact: "pac-filters-row pac-filters-row--compact",
          trailingBox: "pac-filter-box pac-filter-box--action",
        }}
      >
        <span>Campo</span>
      </FiltersRow>,
    );

    expect(container.querySelector(".pac-filters-row--compact")).toBeTruthy();
    expect(container.querySelector(".pac-filter-box--action")).toBeTruthy();
  });
});

describe("FilterInputField", () => {
  it("liga label ao input via htmlFor", () => {
    render(
      <FilterInputField
        classNames={classNames}
        id="dp-competence"
        label="Competência"
        type="month"
        value="2026-07"
        onChange={() => undefined}
      />,
    );

    expect(screen.getByLabelText("Competência")).toHaveProperty("type", "month");
  });
});
