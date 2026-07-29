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

  it("usa NativeCheckboxControl do kit (delpi-ui-native-checkbox)", () => {
    const { container } = render(
      <FilterCheckboxField
        id="filter-native"
        label="OP mãe"
        checkboxLabel="Somente OP's mães"
        checked={false}
        onChange={() => undefined}
        classNames={filterCheckboxFieldPacClasses("pa")}
        labels={LABELS}
      />,
    );

    expect(container.querySelector(".delpi-ui-native-checkbox")).toBeTruthy();
    expect(screen.getByLabelText("Somente OP's mães")).toBeTruthy();
  });
});
