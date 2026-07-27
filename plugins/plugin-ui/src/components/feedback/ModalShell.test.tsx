import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  DELPI_MODAL_HOST_ATTR,
  createHostContainedModalShell,
  createModalShell,
  ModalShell,
  modalShellBemClasses,
} from "./ModalShell";

const modalCss = readFileSync(resolve(process.cwd(), "src/styles/modal.css"), "utf8");
const modalShellCss = readFileSync(resolve(process.cwd(), "src/styles/modal-shell.css"), "utf8");

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
    expect(dialog.className).toContain("delpi-ui-modal-frame");
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

  it("preserva o dimensionamento wide/page definido pelo CSS canônico", () => {
    expect(modalCss).toMatch(
      /\.delpi-ui-modal--page\s*\{[^}]*width:\s*min\(1180px,\s*calc\(100vw - 24px\)\)/s,
    );
    expect(modalShellCss).not.toMatch(
      /\.delpi-ui-modal\s*\{[^}]*(?:width|max-width|max-height)\s*:/s,
    );
  });

  it("permite conter o portal na área do host", () => {
    const content = document.createElement("div");
    content.className = "content";
    content.getBoundingClientRect = () =>
      ({
        top: 40,
        left: 200,
        width: 900,
        height: 600,
        right: 1100,
        bottom: 640,
        x: 200,
        y: 40,
        toJSON() {
          return {};
        },
      }) as DOMRect;

    const host = document.createElement("main");
    host.className = "dashboard-tv-dashboard";
    content.appendChild(host);
    document.body.appendChild(content);

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

    // Geometria inline — fixed no scrollport visível (não absolute no host height:auto).
    expect((portal as HTMLElement).style.position).toBe("fixed");
    expect((portal as HTMLElement).style.width).toBe("900px");
    expect((portal as HTMLElement).style.height).toBe("600px");
    expect((portal as HTMLElement).style.top).toBe("40px");
    expect((portal as HTMLElement).style.left).toBe("200px");
    const overlayEl = dialog.closest(".td-modal-overlay") as HTMLElement;
    expect(overlayEl.style.position).toBe("absolute");
    expect(overlayEl.style.inset).toBe("0px");
    expect(dialog.style.width).toBe("100%");
    expect(dialog.style.height).toBe("100%");
    expect(dialog.style.maxWidth).toBe("none");
    expect(dialog.style.maxHeight).toBe("none");
    // Margem + blur vêm do CSS canônico (não inline — MFE não deve anular padding).
    expect(modalShellCss).toMatch(
      /\.delpi-ui-modal-overlay--contained\s*\{[^}]*padding:\s*12px/s,
    );
    expect(modalShellCss).toMatch(
      /\.delpi-ui-modal-overlay--contained\s*\{[^}]*backdrop-filter:\s*blur\(8px\)/s,
    );

    unmount();
    expect(host.getAttribute(DELPI_MODAL_HOST_ATTR)).toBeNull();
    content.remove();
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

  it("host-fill body permite scroll vertical (overflow:auto) para formulários longos", () => {
    expect(modalShellCss).toMatch(
      /\.delpi-ui-modal--host-fill\s+\.delpi-ui-modal__body[\s\S]*?overflow:\s*auto/s,
    );
  });

  it("createHostContainedModalShell com layout dialog centraliza o card sem host-fill", () => {
    const host = document.createElement("main");
    host.className = "dashboard-tv-dashboard";
    document.body.appendChild(host);

    const HostDialog = createHostContainedModalShell({
      prefix: "td",
      portalScopeClassName: "dashboard-tv-dashboard",
      containedLayout: "dialog",
    });

    const { unmount } = render(
      <HostDialog open title="Aviso" onClose={vi.fn()}>
        <p>Link copiado.</p>
      </HostDialog>,
    );

    const dialog = screen.getByRole("dialog", { name: "Aviso" });
    expect(host.contains(dialog)).toBe(true);
    expect(host.getAttribute(DELPI_MODAL_HOST_ATTR)).toBe("true");
    expect(dialog.classList.contains("delpi-ui-modal--host-fill")).toBe(false);
    expect(dialog.style.width).toBe("");
    expect(dialog.style.height).toBe("");
    expect(dialog.closest(".delpi-ui-modal-overlay--contained-dialog")).toBeTruthy();
    expect(modalShellCss).toMatch(
      /\.delpi-ui-modal-overlay--contained\.delpi-ui-modal-overlay--contained-dialog\s*\{[^}]*align-items:\s*center/s,
    );

    unmount();
    host.remove();
  });
});
