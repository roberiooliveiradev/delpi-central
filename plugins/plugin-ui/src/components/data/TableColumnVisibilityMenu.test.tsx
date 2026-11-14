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

  it("dispara onReorderColumns ao soltar item arrastado", () => {
    const onReorder = vi.fn();
    render(
      <TableColumnVisibilityMenu
        columns={[
          { key: "cliente", label: "Cliente" },
          { key: "pedido", label: "Pedido" },
        ]}
        visibility={{ cliente: true, pedido: true }}
        onToggleColumn={() => undefined}
        onReorderColumns={onReorder}
        onReset={() => undefined}
        labels={LABELS}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Colunas" }));
    const items = document.querySelectorAll(".delpi-ui-table-columns__item");
    expect(items.length).toBe(2);
    fireEvent.dragStart(items[0]!, {
      dataTransfer: { setData: vi.fn(), effectAllowed: "move" },
    });
    fireEvent.drop(items[1]!, {
      dataTransfer: { getData: () => "cliente" },
    });
    expect(onReorder).toHaveBeenCalledWith("cliente", "pedido");
  });

  it("renderiza label na classe canônica do checkbox", () => {
    render(
      <TableColumnVisibilityMenu
        columns={[{ key: "loja", label: "Loja" }]}
        visibility={{ loja: true }}
        onToggleColumn={() => undefined}
        onReset={() => undefined}
        labels={LABELS}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Colunas" }));
    // Painel via AnchoredPanelPortal (document.body) — não usar container.
    expect(document.querySelector(".delpi-ui-native-checkbox__label")?.textContent).toBe("Loja");
  });

  it("renderiza o painel em portal no document.body (não recortado por ancestral com overflow)", () => {
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
    const panel = document.querySelector(".delpi-ui-table-columns__panel--portal");
    expect(panel).toBeTruthy();
    expect(container.contains(panel)).toBe(false);
    expect(document.body.contains(panel)).toBe(true);
    expect(panel?.getAttribute("role")).toBe("dialog");
  });

  it("fecha o painel com Escape", () => {
    render(
      <TableColumnVisibilityMenu
        columns={[{ key: "loja", label: "Loja" }]}
        visibility={{ loja: true }}
        onToggleColumn={() => undefined}
        onReset={() => undefined}
        labels={LABELS}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Colunas" }));
    expect(document.querySelector(".delpi-ui-table-columns__panel--portal")).toBeTruthy();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(document.querySelector(".delpi-ui-table-columns__panel--portal")).toBeFalsy();
  });
});
