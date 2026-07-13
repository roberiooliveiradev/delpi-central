import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ModalShell, modalShellBemClasses } from "./ModalShell";

describe("ModalShell", () => {
  it("não renderiza quando fechado", () => {
    const { container } = render(
      <ModalShell
        open={false}
        title="Confirmar"
        onClose={vi.fn()}
        classNames={modalShellBemClasses("pac")}
      >
        <p>Conteúdo</p>
      </ModalShell>,
    );

    expect(container.innerHTML).toBe("");
  });

  it("renderiza título e corpo quando aberto", () => {
    render(
      <ModalShell open title="Confirmar exclusão" onClose={vi.fn()} classNames={modalShellBemClasses("pac")}>
        <p>Mensagem</p>
      </ModalShell>,
    );

    expect(screen.getByRole("dialog", { name: "Confirmar exclusão" })).toBeTruthy();
    expect(screen.getByText("Mensagem")).toBeTruthy();
  });

  it("inclui footer no BEM padrão", () => {
    expect(modalShellBemClasses("td").footer).toBe("td-modal__footer");
  });

  it("renderiza description e footer quando informados", () => {
    render(
      <ModalShell
        open
        title="Editar meta"
        description="Ajuste os valores do indicador."
        footer={<button type="button">Salvar</button>}
        onClose={vi.fn()}
        classNames={{
          ...modalShellBemClasses("si"),
          headerText: "si-modal__header-text",
          description: "si-modal__description",
        }}
      >
        <p>Corpo</p>
      </ModalShell>,
    );

    expect(screen.getByText("Ajuste os valores do indicador.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Salvar" })).toBeTruthy();
  });

  it("envolve o overlay com portalScopeClassName do plugin", () => {
    render(
      <ModalShell
        open
        title="Remover tela"
        onClose={vi.fn()}
        classNames={modalShellBemClasses("td")}
        portalScopeClassName="dashboard-tv-dashboard"
      >
        <p>Confirmar</p>
      </ModalShell>,
    );

    const dialog = screen.getByRole("dialog", { name: "Remover tela" });
    expect(dialog.closest(".dashboard-tv-dashboard")).toBeTruthy();
    expect(dialog.closest(".td-modal-overlay")).toBeTruthy();
  });
});
