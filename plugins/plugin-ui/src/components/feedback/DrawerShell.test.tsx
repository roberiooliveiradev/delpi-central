import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createHostContainedDrawerShell,
  DrawerShell,
  drawerShellBemClasses,
} from "./DrawerShell";

afterEach(cleanup);

describe("DrawerShell", () => {
  it("não renderiza quando fechado", () => {
    const { container } = render(
      <DrawerShell
        open={false}
        title="Detalhes"
        onClose={vi.fn()}
        classNames={drawerShellBemClasses("si")}
      >
        <p>Conteúdo</p>
      </DrawerShell>,
    );

    expect(container.innerHTML).toBe("");
  });

  it("renderiza título, description e footer quando aberto", () => {
    render(
      <DrawerShell
        open
        title="Editar departamento"
        description="Ajuste metas e responsáveis."
        footer={<button type="button">Salvar</button>}
        onClose={vi.fn()}
        classNames={{
          ...drawerShellBemClasses("si"),
          headerText: "si-drawer__header-text",
          description: "si-drawer__description",
          footer: "si-drawer__footer",
        }}
      >
        <p>Formulário</p>
      </DrawerShell>,
    );

    expect(screen.getByRole("dialog", { name: "Editar departamento" })).toBeTruthy();
    expect(screen.getByText("Ajuste metas e responsáveis.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Salvar" })).toBeTruthy();
    expect(screen.getByText("Formulário")).toBeTruthy();
  });

  it("createHostContainedDrawerShell porta para o root do MFE", () => {
    const host = document.createElement("div");
    host.className = "dashboard-commercial";
    document.body.appendChild(host);

    const HostDrawer = createHostContainedDrawerShell({
      prefix: "cm",
      portalScopeClassName: "dashboard-commercial",
    });

    const { unmount } = render(
      <HostDrawer open title="Linha do pedido" onClose={vi.fn()}>
        <p>Detalhe OP</p>
      </HostDrawer>,
    );

    const dialog = screen.getByRole("dialog", { name: "Linha do pedido" });
    expect(dialog.closest("[data-drawer-contained='true']")).toBeTruthy();
    expect(host.contains(dialog)).toBe(true);

    unmount();
    host.remove();
  });

  it("aceita portalTarget customizado no host do drawer", () => {
    const plugin = document.createElement("div");
    plugin.className = "dashboard-commercial";
    const thread = document.createElement("div");
    thread.className = "cm-room-thread__stage";
    plugin.appendChild(thread);
    document.body.appendChild(plugin);

    const HostDrawer = createHostContainedDrawerShell({
      prefix: "cm",
      portalScopeClassName: "dashboard-commercial",
    });

    const { unmount } = render(
      <HostDrawer
        open
        title="Contexto"
        portalTarget={thread}
        onClose={vi.fn()}
      >
        <p>Sobre</p>
      </HostDrawer>,
    );

    const dialog = screen.getByRole("dialog", { name: "Contexto" });
    expect(thread.contains(dialog)).toBe(true);
    expect(plugin.contains(dialog)).toBe(true);

    unmount();
    plugin.remove();
  });

  it("não cai no root do MFE quando portalTarget explícito ainda é null", () => {
    const host = document.createElement("div");
    host.className = "dashboard-commercial";
    document.body.appendChild(host);

    const HostDrawer = createHostContainedDrawerShell({
      prefix: "cm",
      portalScopeClassName: "dashboard-commercial",
    });

    const { container, unmount } = render(
      <HostDrawer
        open
        title="Contexto"
        portalTarget={null}
        onClose={vi.fn()}
      >
        <p>Sobre</p>
      </HostDrawer>,
    );

    expect(container.innerHTML).toBe("");
    expect(host.querySelector("[role='dialog']")).toBeNull();

    unmount();
    host.remove();
  });

  it("não fecha ao clicar no backdrop por default — só no botão Fechar", () => {
    const onClose = vi.fn();
    render(
      <DrawerShell open title="Detalhes" onClose={onClose} classNames={drawerShellBemClasses("si")}>
        <p>Conteúdo</p>
      </DrawerShell>,
    );

    const backdrop = document.querySelector(".delpi-ui-drawer-root__backdrop") as HTMLElement;
    expect(backdrop.tagName).toBe("DIV");
    fireEvent.click(backdrop);
    expect(onClose).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Fechar" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("fecha no clique do backdrop quando closeOnBackdropClick=true", () => {
    const onClose = vi.fn();
    render(
      <DrawerShell
        open
        title="Painel"
        onClose={onClose}
        closeOnBackdropClick
        classNames={drawerShellBemClasses("si")}
      >
        <p>Ok</p>
      </DrawerShell>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Fechar painel" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
