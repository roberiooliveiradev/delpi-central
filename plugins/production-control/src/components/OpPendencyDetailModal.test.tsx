// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { DemandLine, OpPendencyItem } from "../types";
import { OpPendencyDetailModal, formatOpPendencyQuantity } from "./OpPendencyDetailModal";

vi.mock("./PpcConfirmModal", () => ({
  HostContainedFitDialog: ({
    open, title, onClose, children,
  }: { open: boolean; title: string; onClose: () => void; children: ReactNode }) =>
    open ? (
      <div role="dialog" aria-label={title}>
        {children}
        <button type="button" onClick={onClose} aria-label="Fechar cabeçalho">X</button>
      </div>
    ) : null,
}));

const DEMAND: DemandLine = {
  id: "02|MYWEG|R1",
  branch: "02",
  sales_order: "MYWEG",
  line_item: "R1",
  customer_name: "WEG Linhares",
  customer_code: "000001",
  customer_store: "09",
  customer_order: "COL-01",
  order_type: "N",
  product_code: "90263964",
  unit: "MI",
  ordered_quantity: 0.3,
  delivered_quantity: 0,
  open_quantity: 0.3,
  due_date: "2026-11-20",
  dispatch_date: null,
  product_stock: 0.05,
  allocated_stock: 0.05,
  covered_by_orders: 0,
  uncovered_quantity: 0.25,
  covering_orders: [],
  coverage_date: null,
  status: "at_risk",
  days_late: 0,
  source: "myweg",
  planning: true,
};

const PENDENCY: OpPendencyItem = {
  id: "02|include-production-order|90263964",
  kind: "include_production_order",
  branch: "02",
  product_code: "90263964",
  unit: "MI",
  required_date: "2026-11-20",
  suggested_op_date: "2026-11-18",
  next_uncovered_quantity: 0.25,
  next_uncovered_pieces: 250,
  total_uncovered_quantity: 0.4,
  total_uncovered_pieces: 400,
  demand_count: 2,
  origins: ["myweg", "protheus"],
  schedule: [
    {
      required_date: "2026-11-20",
      suggested_op_date: "2026-11-18",
      uncovered_quantity: 0.25,
      uncovered_pieces: 250,
      demand_count: 1,
      lines: [DEMAND],
    },
    {
      required_date: "2026-11-25",
      suggested_op_date: "2026-11-23",
      uncovered_quantity: 0.15,
      uncovered_pieces: 150,
      demand_count: 1,
      lines: [{
        ...DEMAND,
        id: "02|P01|01",
        source: "protheus",
        sales_order: "P01",
        line_item: "01",
        due_date: "2026-11-25",
        customer_name: "Cliente ERP",
        uncovered_quantity: 0.15,
      }],
    },
  ],
};

afterEach(cleanup);

describe("OpPendencyDetailModal #1548", () => {
  it("mostra a data sugerida, quantidade da primeira data e total sem antecipar tudo", () => {
    render(<OpPendencyDetailModal item={PENDENCY} branch="02" onClose={vi.fn()} />);
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText("90263964")).toBeTruthy();
    expect(within(dialog).getAllByText("18/11/2026").length).toBeGreaterThan(0);
    expect(within(dialog).getAllByText("250 peças").length).toBeGreaterThan(0);
    expect(within(dialog).getByText("400 peças")).toBeTruthy();
    expect(within(dialog).getByText("WEG Linhares")).toBeTruthy();
    expect(within(dialog).getByText("Cliente ERP")).toBeTruthy();
    expect(within(dialog).getByText(/P01\/01/)).toBeTruthy();
  });

  it("não confunde MI com peças e não presume a unidade ausente", () => {
    expect(formatOpPendencyQuantity(26, 0.026, "MI")).toBe("26 peças");
    expect(formatOpPendencyQuantity(null, 0.026, "UNSPECIFIED")).toContain("unidade ERP não confirmada");
  });

  it("fecha pelo rodapé", () => {
    const onClose = vi.fn();
    render(<OpPendencyDetailModal item={PENDENCY} branch="02" onClose={onClose} />);
    fireEvent.click(screen.getByRole("button", { name: "Fechar" }));
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("button", { name: "Abrir em Demandas" })).toBeTruthy();
  });

  it("não renderiza quando nenhuma pendência está selecionada", () => {
    const { container } = render(
      <OpPendencyDetailModal item={null} branch="02" onClose={vi.fn()} />,
    );
    expect(container.innerHTML).toBe("");
  });
});
