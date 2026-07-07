import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ConfirmModalPanel, confirmModalPacClasses } from "./ConfirmModalPanel";

afterEach(() => {
  cleanup();
});

describe("ConfirmModalPanel", () => {
  it("renderiza mensagem e botões com classes BEM", () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();
    const classNames = confirmModalPacClasses();

    render(
      <ConfirmModalPanel
        message="Excluir registro?"
        confirmLabel="Excluir"
        cancelLabel="Voltar"
        classNames={classNames}
        onConfirm={onConfirm}
        onCancel={onCancel}
      />,
    );

    expect(screen.getByText("Excluir registro?").className).toBe(classNames.message);
    expect(screen.getByRole("button", { name: "Excluir" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Voltar" })).toBeTruthy();
  });

  it("aplica classe danger no botão de confirmar", () => {
    const classNames = confirmModalPacClasses();

    render(
      <ConfirmModalPanel
        message="Ação irreversível"
        variant="danger"
        classNames={classNames}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Confirmar" }).className).toBe(
      classNames.confirmButtonDanger,
    );
  });
});
