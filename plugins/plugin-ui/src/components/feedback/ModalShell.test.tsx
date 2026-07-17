import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  createModalShell,
  ModalShell,
  modalShellBemClasses,
} from "./ModalShell";

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

  it("emite dual-class canônico delpi-ui-modal*", () => {
    const classes = modalShellBemClasses("td");
    expect(classes.dialog).toContain("td-modal");
    expect(classes.dialog).toContain("delpi-ui-modal");
    expect(classes.overlay).toContain("delpi-ui-modal-overlay");
    expect(classes.description).toContain("delpi-ui-modal__description");
    expect(classes.footer).toContain("td-modal__footer");
    expect(classes.footer).toContain("delpi-ui-modal__footer");
  });

  it("renderiza description e footer quando informados", () => {
    render(
      <ModalShell
        open
        title="Editar meta"
        description="Ajuste os valores do indicador."
        footer={<button type="button">Salvar</button>}
        onClose={vi.fn()}
        classNames={modalShellBemClasses("si")}
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
    expect(dialog.className).toContain("delpi-ui-modal");
  });

  it("createModalShell aplica variante page com dual-class", () => {
    const PageModal = createModalShell({
      prefix: "ess",
      variant: "page",
      portalScopeClassName: "dashboard-estoque-seguranca",
    });

    render(
      <PageModal open title="Detalhe" onClose={vi.fn()}>
        <p>Extrato</p>
      </PageModal>,
    );

    const dialog = screen.getByRole("dialog", { name: "Detalhe" });
    expect(dialog.className).toContain("ess-modal--page");
    expect(dialog.className).toContain("delpi-ui-modal--page");
    expect(dialog.closest(".dashboard-estoque-seguranca")).toBeTruthy();
  });
});
