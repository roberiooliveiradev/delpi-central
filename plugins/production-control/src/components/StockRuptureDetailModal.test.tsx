// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { StockRupturePendencyItem } from "../types";
import {
  StockRuptureDetailModal,
  formatMaterialQuantity,
} from "./StockRuptureDetailModal";

vi.mock("./PpcConfirmModal", () => ({
  HostContainedFitDialog: ({
    open, title, children, onClose,
  }: {
    open: boolean;
    title: string;
    children: ReactNode;
    onClose: () => void;
  }) => open ? (
    <div role="dialog" aria-label={title}>
      {children}
      <button type="button" aria-label="Fechar no cabeçalho" onClick={onClose}>X</button>
    </div>
  ) : null,
}));

const ITEM: StockRupturePendencyItem = {
  id: "02|stock-rupture|10080001",
  kind: "stock_rupture",
  branch: "02",
  product_code: "10080001",
  product_description: "Cabo de cobre",
  unit: "MT",
  first_shortage_date: "2026-11-12",
  available_stock: 30.5,
  shortage_balance: -12.25,
  last_inventory_date: "2026-11-03",
  next_purchase: "PC 12345, previsto para 13/11",
  observation: "Validar com suprimentos",
  provider_key: "safety_stock_shortage_30d",
};

afterEach(cleanup);

describe("StockRuptureDetailModal #1549", () => {
  it("exibe projeção, unidade original, compra e observações", () => {
    render(
      <StockRuptureDetailModal item={ITEM} branch="02" asOf="2026-11-09" onClose={vi.fn()} />,
    );
    const dialog = screen.getByRole("dialog", { name: "Ruptura de estoque" });
    expect(within(dialog).getByText("10080001")).toBeTruthy();
    expect(within(dialog).getByText("Cabo de cobre")).toBeTruthy();
    expect(within(dialog).getByText("12/11/2026")).toBeTruthy();
    expect(within(dialog).getByText("30,5 MT")).toBeTruthy();
    expect(within(dialog).getByText("-12,25 MT")).toBeTruthy();
    expect(within(dialog).getByText("03/11/2026")).toBeTruthy();
    expect(within(dialog).getByText("PC 12345, previsto para 13/11")).toBeTruthy();
    expect(within(dialog).getByText("Validar com suprimentos")).toBeTruthy();
    const link = within(dialog).getByRole("link", { name: "Abrir Estoque de Segurança" });
    expect(link.getAttribute("href")).toBe("/apps/estoque-seguranca?q=10080001");
  });

  it("mantém quantidades de matéria-prima na unidade original", () => {
    expect(formatMaterialQuantity(-125.1234, "KG")).toBe("-125,1234 KG");
    expect(formatMaterialQuantity(0.026, "MI")).toBe("0,026 MI");
    expect(formatMaterialQuantity(null, "MT")).toBe("—");
  });

  it("identifica ruptura vencida e esconde observação vazia", () => {
    render(
      <StockRuptureDetailModal
        item={{ ...ITEM, first_shortage_date: "2026-11-05", observation: "" }}
        branch="02"
        asOf="2026-11-09"
        onClose={vi.fn()}
      />,
    );
    expect(screen.getByText("Ruptura identificada em")).toBeTruthy();
    expect(screen.queryByText("Observações")).toBeNull();
  });

  it("não mostra dados de filial diferente ou modal sem item", () => {
    const first = render(
      <StockRuptureDetailModal item={ITEM} branch="01" asOf={null} onClose={vi.fn()} />,
    );
    expect(first.container.innerHTML).toBe("");
    const second = render(
      <StockRuptureDetailModal item={null} branch="02" asOf={null} onClose={vi.fn()} />,
    );
    expect(second.container.innerHTML).toBe("");
  });

  it("fecha pelo rodapé", () => {
    const onClose = vi.fn();
    render(
      <StockRuptureDetailModal item={ITEM} branch="02" asOf="2026-11-09" onClose={onClose} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Fechar" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
