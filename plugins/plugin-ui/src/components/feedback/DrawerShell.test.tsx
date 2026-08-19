import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  createHostContainedDrawerShell,
  DrawerShell,
  drawerShellBemClasses,
} from "./DrawerShell";

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
    thread.className = "cm-room-thread";
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
});
