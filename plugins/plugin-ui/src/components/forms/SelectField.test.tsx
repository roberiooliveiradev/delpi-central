import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  SelectControl,
  selectControlBemClasses,
} from "./SelectField";

const LABELS = {
  searchPlaceholder: "Buscar…",
  emptyOptions: "Nenhuma opção encontrada.",
  searchAriaLabel: (label?: string) => (label ? `Buscar ${label}` : "Buscar opções"),
};

afterEach(() => {
  cleanup();
});

describe("SelectControl", () => {
  it("renderiza trigger com placeholder", () => {
    render(
      <SelectControl
        options={[{ value: "a", label: "Opção A" }]}
        value=""
        onChange={vi.fn()}
        placeholder="Selecione…"
        ariaLabel="Status"
        classNames={selectControlBemClasses("ds")}
        labels={LABELS}
      />,
    );

    expect(screen.getByRole("button", { name: "Status" })).toBeTruthy();
    expect(screen.getByText("Selecione…")).toBeTruthy();
  });
});
