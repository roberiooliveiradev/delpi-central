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

    expect(screen.getByText("Excluir registro?").className).toContain("pac-confirm-modal__message");
    expect(screen.getByRole("button", { name: "Excluir" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Voltar" })).toBeTruthy();
    expect(document.querySelector(".pac-confirm-modal__icon")).toBeTruthy();
  });

  it("aplica classe danger no botão de confirmar e no ícone", () => {
    const classNames = confirmModalPacClasses();

    const { container } = render(
      <ConfirmModalPanel
        message="Ação irreversível"
        variant="danger"
        classNames={classNames}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Confirmar" }).className).toContain("pac-danger-btn");
    expect(container.querySelector(".pac-confirm-modal--danger")).toBeTruthy();
    expect(container.querySelector(".pac-confirm-modal__icon--danger")).toBeTruthy();
  });
});
