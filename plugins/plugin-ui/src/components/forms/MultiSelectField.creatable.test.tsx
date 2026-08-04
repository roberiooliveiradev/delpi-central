import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createDashboardCreatableMultiSelectField,
  multiSelectCreatablePacClasses,
  type MultiSelectFieldLabels,
} from "./MultiSelectField";

const LABELS = {
  emptyLabel: "Selecione ou digite…",
  searchPlaceholder: "Buscar ou adicionar…",
  selectVisible: "Marcar visíveis",
  clear: "Limpar",
  emptyOptions: "Nenhuma opção encontrada.",
  emptyOptionsCreatable: "Pressione Enter ou use o botão acima.",
  multipleSelected: (count: number) => `${count} item(ns) selecionado(s)`,
  createOption: (value: string) => `Adicionar «${value.trim()}»`,
} satisfies MultiSelectFieldLabels;

const CreatableMultiSelectField = createDashboardCreatableMultiSelectField({
  classNames: multiSelectCreatablePacClasses("pac"),
  labels: LABELS,
});

afterEach(() => {
  cleanup();
});

describe("createDashboardCreatableMultiSelectField", () => {
  it("renderiza campo creatable com tags e busca", () => {
    render(
      <CreatableMultiSelectField
        label="Tags"
        hint="Adicione tags"
        options={[{ value: "a", label: "Alpha" }]}
        selectedValues={["a"]}
        onChange={() => undefined}
      />,
    );

    expect(screen.getByText("Tags")).toBeTruthy();
    expect(document.querySelector(".pac-field--creatable-multi")).toBeTruthy();
    expect(document.querySelector(".pac-tag-list")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-tag-list")).toBeTruthy();
  });

  it("aceita placeholder customizado", () => {
    const { container } = render(
      <CreatableMultiSelectField
        label="Categoria"
        placeholder="Digite…"
        selectedValues={[]}
        onChange={() => undefined}
      />,
    );

    fireEvent.click(container.querySelector(".pac-multi-select__trigger") as Element);
    expect(screen.getByPlaceholderText("Digite…")).toBeTruthy();
  });

  it("emite classes canônicas de chip e respeita maxSelected=1", () => {
    const onChange = vi.fn();
    const { container } = render(
      <CreatableMultiSelectField
        label="Família"
        options={[
          { value: "ia", label: "ia" },
          { value: "automacao", label: "automacao" },
        ]}
        selectedValues={["ia"]}
        maxSelected={1}
        onChange={onChange}
      />,
    );

    expect(document.querySelector(".delpi-ui-tag-list")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-tag-chip")).toBeTruthy();

    fireEvent.click(container.querySelector(".pac-multi-select__trigger") as Element);
    const boxes = container.querySelectorAll('.pac-multi-select__option input[type="checkbox"]');
    expect(boxes.length).toBeGreaterThanOrEqual(2);
    fireEvent.click(boxes[1] as Element);
    expect(onChange).toHaveBeenCalledWith(["automacao"]);
  });
});
