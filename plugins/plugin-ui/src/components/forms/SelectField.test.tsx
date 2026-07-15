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
  it("emite prefix + delpi-ui-select nas classNames", () => {
    const cn = selectControlBemClasses("ds");
    expect(cn.root).toBe("ds-select delpi-ui-select");
    expect(cn.trigger).toContain("delpi-ui-select__trigger");
    expect(cn.panel).toContain("delpi-ui-select__panel");
  });

  it("não duplica quando o prefixo já é delpi-ui", () => {
    const cn = selectControlBemClasses("delpi-ui");
    expect(cn.root).toBe("delpi-ui-select");
    expect(cn.trigger).toBe("delpi-ui-select__trigger");
  });

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
