import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  EditableSectionCard,
  editableSectionCardBemClasses,
} from "./EditableSectionCard";

const LABELS = {
  edit: "Editar",
  save: "Salvar",
  saving: "Salvando…",
  cancel: "Cancelar",
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

afterEach(() => {
  cleanup();
});

describe("EditableSectionCard", () => {
  it("renderiza conteúdo de leitura e botão editar", () => {
    render(
      <EditableSectionCard
        title="Identificação"
        isEditing={false}
        onEdit={vi.fn()}
        onCancel={vi.fn()}
        readContent={<p>Leitura</p>}
        editContent={<p>Edição</p>}
        classNames={editableSectionCardBemClasses("kz")}
        labels={LABELS}
      />,
    );

    expect(screen.getByText("Identificação")).toBeTruthy();
    expect(screen.getByText("Leitura")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Editar/i })).toBeTruthy();
  });

  it("exibe ações de salvar e cancelar em modo edição", () => {
    render(
      <EditableSectionCard
        title="Dados"
        isEditing={true}
        onEdit={vi.fn()}
        onCancel={vi.fn()}
        onSave={vi.fn()}
        readContent={<p>Leitura</p>}
        editContent={<p>Edição</p>}
        classNames={editableSectionCardBemClasses("kz")}
        labels={LABELS}
      />,
    );

    expect(screen.getByText("Edição")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Salvar/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Cancelar/i })).toBeTruthy();
  });
});
