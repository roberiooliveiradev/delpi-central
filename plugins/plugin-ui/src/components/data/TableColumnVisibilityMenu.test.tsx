import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TableColumnVisibilityMenu } from "./TableColumnVisibilityMenu";

const LABELS = {
  trigger: "Colunas",
  panelTitle: "Exibir colunas",
  reset: "Restaurar",
  hint: "Escolha quais colunas exibir.",
  columnAriaLabel: (columnLabel: string) => `Exibir coluna ${columnLabel}`,
  panelAriaLabel: "Colunas visíveis",
};

afterEach(() => {
  cleanup();
});

describe("TableColumnVisibilityMenu", () => {
  it("abre o painel e mostra rótulos das colunas (não só checkboxes)", () => {
    render(
      <TableColumnVisibilityMenu
        columns={[
          { key: "cliente", label: "Cliente" },
          { key: "pedido", label: "Pedido" },
        ]}
        visibility={{ cliente: true, pedido: true }}
        onToggleColumn={() => undefined}
        onReset={() => undefined}
        labels={LABELS}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Colunas" }));
    expect(screen.getByText("Cliente")).toBeTruthy();
    expect(screen.getByText("Pedido")).toBeTruthy();
    expect(screen.getByText("Exibir colunas")).toBeTruthy();
  });

  it("dispara onToggleColumn e impede desmarcar a última coluna", () => {
    const onToggle = vi.fn();
    render(
      <TableColumnVisibilityMenu
        columns={[
          { key: "cliente", label: "Cliente" },
          { key: "pedido", label: "Pedido" },
        ]}
        visibility={{ cliente: true, pedido: false }}
        onToggleColumn={onToggle}
        onReset={() => undefined}
        labels={LABELS}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Colunas" }));
    const lastVisible = screen.getByRole("checkbox", {
      name: "Exibir coluna Cliente",
    }) as HTMLInputElement;
    expect(lastVisible.disabled).toBe(true);

    fireEvent.click(screen.getByRole("checkbox", { name: "Exibir coluna Pedido" }));
    expect(onToggle).toHaveBeenCalledWith("pedido", true);
  });

  it("renderiza label na classe canônica do checkbox", () => {
    const { container } = render(
      <TableColumnVisibilityMenu
        columns={[{ key: "loja", label: "Loja" }]}
        visibility={{ loja: true }}
        onToggleColumn={() => undefined}
        onReset={() => undefined}
        labels={LABELS}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Colunas" }));
    expect(container.querySelector(".delpi-ui-native-checkbox__label")?.textContent).toBe("Loja");
  });
});
