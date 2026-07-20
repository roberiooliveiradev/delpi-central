import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { FilterInputField, FilterSelectField, FiltersRow, filterBoxBemClasses, filtersRowBemClasses } from "./FiltersRow";
import { selectControlBemClasses } from "../forms/SelectField";

const classNames = {
  row: "dp-filters-row",
  rowExtended: "dp-filters-row dp-filters-row--extended",
  filterBox: "dp-filter-box dp-field",
  fieldLabel: "dp-field__label",
};

const selectClassNames = selectControlBemClasses("dp");

describe("filtersRowBemClasses / filterBoxBemClasses", () => {
  it("emite dual-class do kit", () => {
    const cn = filtersRowBemClasses("ds");
    expect(cn.row).toBe("ds-filters-row delpi-ui-filters-row");
    expect(cn.filterBox).toContain("delpi-ui-filter-box");
    expect(filterBoxBemClasses("ds", "wide")).toContain("delpi-ui-filter-box--wide");
  });
});

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
        trailing={
          <>
            <button type="button">Baixar</button>
            <button type="button">Buscar</button>
          </>
        }
        classNames={{
          row: "pac-filters-row",
          rowExtended: "pac-filters-row pac-filters-row--extended",
          rowCompact: "pac-filters-row pac-filters-row--compact",
          trailingBox: "pac-filter-box pac-filter-box--action delpi-ui-filter-box--action",
        }}
      >
        <span>Campo</span>
      </FiltersRow>,
    );

    expect(container.querySelector(".pac-filters-row--compact")).toBeTruthy();
    const trailing = container.querySelector(".delpi-ui-filter-box--action");
    expect(trailing).toBeTruthy();
    expect(trailing?.querySelectorAll("button")).toHaveLength(2);
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

describe("FilterSelectField", () => {
  it("usa SelectControl em vez de select nativo", () => {
    const onChange = vi.fn();
    const { container } = render(
      <FilterSelectField
        classNames={classNames}
        selectClassNames={selectClassNames}
        id="dp-type"
        label="Tipo"
        value="a"
        onChange={onChange}
        options={[
          { value: "a", label: "Opção A" },
          { value: "b", label: "Opção B" },
        ]}
        placeholderOption="Todos"
      />,
    );

    expect(container.querySelector("select")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Tipo" }));
    fireEvent.click(screen.getByRole("button", { name: "Opção B" }));
    expect(onChange).toHaveBeenCalledWith("b");
  });

  it("envolve o painel portado com escopo do dashboard (CSS do plugin)", () => {
    render(
      <div className="dashboard-quality">
        <FilterSelectField
          classNames={classNames}
          selectClassNames={selectControlBemClasses("dq")}
          id="dq-ppm"
          label="Produto (PPM)"
          value="all"
          onChange={() => undefined}
          options={[
            { value: "all", label: "Todos os produtos" },
            { value: "plugs", label: "Plugues (9048*)" },
          ]}
        />
      </div>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Produto (PPM)" }));
    const scope = document.body.querySelector(".dashboard-quality.delpi-ui-shape-theme-host");
    expect(scope).toBeTruthy();
    expect(scope?.querySelector(".dq-select__panel--portal")).toBeTruthy();
    expect(scope?.querySelector(".dq-select__list")).toBeTruthy();
  });
});
