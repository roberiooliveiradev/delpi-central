import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import {
  createDashboardMultiSelectField,
  multiSelectBemClasses,
  type MultiSelectFieldLabels,
} from "./MultiSelectField";

const LABELS = {
  emptyLabel: "Todos",
  searchPlaceholder: "Buscar…",
  selectVisible: "Marcar visíveis",
  clear: "Limpar",
  emptyOptions: "Nenhuma opção encontrada.",
  multipleSelected: (count: number) => `${count} selecionado(s)`,
} satisfies MultiSelectFieldLabels;

const MultiSelectField = createDashboardMultiSelectField({ prefix: "dc", labels: LABELS });

afterEach(() => {
  cleanup();
});

describe("multiSelectBemClasses", () => {
  it("usa ação canônica delpi-ui sem ghost-btn de toolbar", () => {
    const cn = multiSelectBemClasses("dc");
    expect(cn.actionButton).toBe("delpi-ui-multi-select__action");
    expect(cn.actionButton).not.toContain("ghost-btn");
    expect(cn.actions).toContain("delpi-ui-multi-select__actions");
    expect(cn.panel).toContain("delpi-ui-multi-select__panel");
    expect(cn.trigger).toContain("delpi-ui-multi-select__trigger");
    expect(cn.option).toContain("delpi-ui-multi-select__option");
    expect(cn.multiSelect).toContain("delpi-ui-multi-select");
  });
});

describe("MultiSelectField actions", () => {
  it("renderiza botões de ação com classe canônica idêntica", () => {
    render(
      <MultiSelectField
        label="Unidade"
        searchable
        options={[
          { value: "01", label: "Santa Catarina" },
          { value: "02", label: "Espírito Santo" },
        ]}
        selectedValues={[]}
        onChange={() => undefined}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Todos" }));
    const selectVisible = screen.getByRole("button", { name: "Marcar visíveis" });
    const clear = screen.getByRole("button", { name: "Limpar" });
    expect(selectVisible.className).toContain("delpi-ui-multi-select__action");
    expect(clear.className).toContain("delpi-ui-multi-select__action");
    expect(selectVisible.className).toEqual(clear.className);
  });
});
