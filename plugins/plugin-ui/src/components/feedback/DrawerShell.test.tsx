import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DrawerShell, drawerShellBemClasses } from "./DrawerShell";

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
});
