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

describe("editableSectionCardBemClasses", () => {
  it("emite dual-class do kit (header + ghost) para layout e botão", () => {
    const classes = editableSectionCardBemClasses("kz");
    expect(classes.section).toContain("delpi-ui-card");
    expect(classes.section).toContain("delpi-ui-section-card");
    expect(classes.header).toContain("delpi-ui-section-card__header");
    expect(classes.actions).toContain("delpi-ui-section-card__actions");
    expect(classes.ghostButton).toBe("kz-ghost-btn delpi-ui-ghost-btn");
  });
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
    const edit = screen.getByRole("button", { name: /Editar/i });
    expect(edit).toBeTruthy();
    expect(edit.className).toContain("delpi-ui-ghost-btn");
  });

  it("exibe ações de salvar e cancelar em modo edição quando dirty", () => {
    render(
      <EditableSectionCard
        title="Dados"
        isEditing={true}
        onEdit={vi.fn()}
        onCancel={vi.fn()}
        onSave={vi.fn()}
        dirty
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

  it("oculta Salvar sem alterações no card", () => {
    render(
      <EditableSectionCard
        title="Dados"
        isEditing={true}
        onEdit={vi.fn()}
        onCancel={vi.fn()}
        onSave={vi.fn()}
        dirty={false}
        readContent={<p>Leitura</p>}
        editContent={<p>Edição</p>}
        classNames={editableSectionCardBemClasses("kz")}
        labels={LABELS}
      />,
    );

    expect(screen.queryByRole("button", { name: /Salvar/i })).toBeNull();
    expect(screen.getByRole("button", { name: /Cancelar/i })).toBeTruthy();
  });
});
