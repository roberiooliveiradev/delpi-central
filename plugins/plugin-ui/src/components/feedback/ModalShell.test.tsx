import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  DELPI_MODAL_HOST_ATTR,
  createHostContainedModalShell,
  createModalShell,
  ModalShell,
  modalShellBemClasses,
} from "./ModalShell";

afterEach(cleanup);

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

  it("permite conter o portal na área do host", () => {
    const host = document.createElement("main");
    host.className = "dashboard-tv-dashboard";
    document.body.appendChild(host);

    const { unmount } = render(
      <ModalShell
        open
        title="Preparar dados"
        onClose={vi.fn()}
        classNames={modalShellBemClasses("td")}
        portalScopeClassName="dashboard-tv-dashboard"
        portalTarget={host}
        containedInPortalTarget
      >
        <p>Consulta</p>
      </ModalShell>,
    );

    const dialog = screen.getByRole("dialog", { name: "Preparar dados" });
    const portal = dialog.closest("[data-modal-contained='true']");
    expect(host.contains(dialog)).toBe(true);
    expect(portal).toBeTruthy();
    expect(portal?.classList.contains("delpi-ui-modal-portal--contained")).toBe(true);
    expect(dialog.classList.contains("delpi-ui-modal--host-fill")).toBe(true);
    expect(dialog.closest(".delpi-ui-modal-overlay--contained")).toBeTruthy();
    expect(host.getAttribute(DELPI_MODAL_HOST_ATTR)).toBe("true");

    // Geometria inline — CSS `.dashboard-x .td-modal` do MFE não pode vencer.
    expect((portal as HTMLElement).style.position).toBe("absolute");
    const overlayEl = dialog.closest(".td-modal-overlay") as HTMLElement;
    expect(overlayEl.style.position).toBe("absolute");
    expect(overlayEl.style.padding).toBe("0px");
    expect(dialog.style.width).toBe("100%");
    expect(dialog.style.height).toBe("100%");
    expect(dialog.style.maxWidth).toBe("none");
    expect(dialog.style.maxHeight).toBe("none");

    unmount();
    expect(host.getAttribute(DELPI_MODAL_HOST_ATTR)).toBeNull();
    host.remove();
  });

  it("createHostContainedModalShell resolve o root do MFE automaticamente", () => {
    const host = document.createElement("main");
    host.className = "dashboard-tv-dashboard";
    document.body.appendChild(host);

    const HostModal = createHostContainedModalShell({
      prefix: "td",
      portalScopeClassName: "dashboard-tv-dashboard",
    });

    const { unmount } = render(
      <HostModal open title="Preparar dados — M DELPI" onClose={vi.fn()}>
        <p>Workbench</p>
      </HostModal>,
    );

    const dialog = screen.getByRole("dialog", { name: "Preparar dados — M DELPI" });
    expect(host.contains(dialog)).toBe(true);
    expect(host.getAttribute(DELPI_MODAL_HOST_ATTR)).toBe("true");
    expect(dialog.classList.contains("delpi-ui-modal--host-fill")).toBe(true);

    unmount();
    host.remove();
  });
});
