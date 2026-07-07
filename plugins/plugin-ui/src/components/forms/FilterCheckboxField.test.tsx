import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  FilterCheckboxField,
  filterCheckboxFieldPacClasses,
} from "./FilterCheckboxField";

const LABELS = {
  defaultCheckboxLabel: "Ativar filtro",
};

afterEach(() => {
  cleanup();
});

describe("FilterCheckboxField", () => {
  it("renderiza label e checkbox com rótulo padrão", () => {
    render(
      <FilterCheckboxField
        id="filter-overdue"
        label="Somente atrasadas"
        checked={false}
        onChange={() => undefined}
        classNames={filterCheckboxFieldPacClasses("pac")}
        labels={LABELS}
      />,
    );

    expect(screen.getByText("Somente atrasadas")).toBeTruthy();
    expect(screen.getByLabelText("Ativar filtro")).toBeTruthy();
  });

  it("usa checkboxLabel customizado e propaga onChange", () => {
    const onChange = vi.fn();
    render(
      <FilterCheckboxField
        id="filter-completed"
        label="Mostrar concluídas"
        checkboxLabel="Incluir concluídas"
        checked={false}
        onChange={onChange}
        classNames={filterCheckboxFieldPacClasses("pac")}
        labels={LABELS}
      />,
    );

    fireEvent.click(screen.getByLabelText("Incluir concluídas"));
    expect(onChange).toHaveBeenCalledWith(true);
  });
});
