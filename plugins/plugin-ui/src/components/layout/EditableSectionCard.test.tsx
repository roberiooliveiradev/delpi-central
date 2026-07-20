import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  EditableSectionCard,
  createDashboardEditableSectionCardPac,
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

describe("createDashboardEditableSectionCardPac", () => {
  it("botão Editar/Anexar usa dual-class delpi-ui-ghost-btn (não só prefix-ghost-btn)", () => {
    const PacCard = createDashboardEditableSectionCardPac({
      prefix: "pac",
      labels: {
        ...LABELS,
        titleHelpAriaLabel: LABELS.titleHelpAriaLabel,
      },
    });

    render(
      <PacCard
        title="Status do plano"
        isEditing={false}
        onEdit={vi.fn()}
        onCancelEdit={vi.fn()}
        readContent={<p>Leitura</p>}
        editContent={<p>Edição</p>}
        editLabel="Anexar"
      />,
    );

    const edit = screen.getByRole("button", { name: /Anexar/i });
    expect(edit.className).toContain("pac-ghost-btn");
    expect(edit.className).toContain("delpi-ui-ghost-btn");
    expect(edit.querySelector("svg")).toBeTruthy();
  });

  it("CSS canônico do ghost garante flex row + gap (svg block do portal)", () => {
    const css = readFileSync(resolve(process.cwd(), "src/styles/pagination.css"), "utf8");
    expect(css).toMatch(/\.delpi-ui-ghost-btn\s*\{[^}]*display:\s*inline-flex/s);
    expect(css).toMatch(/\.delpi-ui-ghost-btn\s*\{[^}]*flex-direction:\s*row/s);
    expect(css).toMatch(/\.delpi-ui-ghost-btn\s*\{[^}]*gap:\s*8px/s);
    expect(css).toMatch(/\.delpi-ui-ghost-btn\s*>\s*svg\s*\{[^}]*flex-shrink:\s*0/s);
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

  it("ao cancelar remonta o conteúdo e descarta estado interno do draft", async () => {
    const { useState } = await import("react");
    const { fireEvent } = await import("@testing-library/react");

    function DraftProbe({ mode }: { mode: "read" | "edit" }) {
      const [text, setText] = useState("original");
      return (
        <div>
          <span data-testid="draft-value">{text}</span>
          <span data-testid="draft-mode">{mode}</span>
          {mode === "edit" ? (
            <button type="button" onClick={() => setText("alterado")}>
              Mudar
            </button>
          ) : null}
        </div>
      );
    }

    const onCancel = vi.fn();
    const { rerender } = render(
      <EditableSectionCard
        title="Escopo"
        isEditing={true}
        onEdit={vi.fn()}
        onCancel={onCancel}
        readContent={<DraftProbe mode="read" />}
        editContent={<DraftProbe mode="edit" />}
        classNames={editableSectionCardBemClasses("kz")}
        labels={LABELS}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Mudar/i }));
    expect(screen.getByTestId("draft-value").textContent).toBe("alterado");

    rerender(
      <EditableSectionCard
        title="Escopo"
        isEditing={false}
        onEdit={vi.fn()}
        onCancel={onCancel}
        readContent={<DraftProbe mode="read" />}
        editContent={<DraftProbe mode="edit" />}
        classNames={editableSectionCardBemClasses("kz")}
        labels={LABELS}
      />,
    );

    expect(screen.getByTestId("draft-mode").textContent).toBe("read");
    expect(screen.getByTestId("draft-value").textContent).toBe("original");
  });
});
