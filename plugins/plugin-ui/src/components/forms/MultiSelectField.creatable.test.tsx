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
});
