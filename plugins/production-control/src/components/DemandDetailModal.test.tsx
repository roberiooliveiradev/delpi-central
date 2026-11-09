// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { DemandLine } from "../types";
import { DemandDetailModal } from "./DemandDetailModal";

vi.mock("./PpcConfirmModal", () => ({
  HostContainedFitDialog: ({
    open,
    title,
    children,
    onClose,
  }: {
    open: boolean;
    title: string;
    children: ReactNode;
    onClose: () => void;
  }) =>
    open ? (
      <div role="dialog" aria-label={title}>
        <h2>{title}</h2>
        {children}
        <button type="button" onClick={onClose} aria-label="Fechar pelo cabeçalho">
          X
        </button>
      </div>
    ) : null,
}));

const DEMAND: DemandLine = {
  id: "02|MYWEG|r1",
  branch: "02",
  sales_order: "MYWEG",
  line_item: "r1",
  customer_name: "WEG Linhares",
  customer_code: "000001",
  customer_store: "09",
  customer_order: "a692345c-4d11-4bd6-8b6d-4b96ce505634",
  order_type: "myweg",
  product_code: "90263964",
  ordered_quantity: 0.026,
  delivered_quantity: 0,
  open_quantity: 0.026,
  due_date: "2026-10-28",
  dispatch_date: null,
  product_stock: 0,
  allocated_stock: 0,
  covered_by_orders: 0.026,
  uncovered_quantity: 0,
  covering_orders: [
    {
      production_order: "11286701001",
      quantity: 0.026,
      expected_date: "2026-11-09",
      observation: "Corte previsto para o turno da manhã.",
    },
  ],
  coverage_date: "2026-11-09",
  status: "late",
  days_late: 12,
  source: "myweg",
  planning: true,
  op_coverage_incomplete: false,
};

afterEach(cleanup);

describe("DemandDetailModal #1547", () => {
  it("exibe os blocos essenciais, a OP e sua observação", () => {
    render(<DemandDetailModal line={DEMAND} branch="02" onClose={() => undefined} />);
    expect(screen.getByRole("dialog", { name: "Linha da demanda" })).toBeTruthy();
    expect(screen.getByText("90263964")).toBeTruthy();
    expect(screen.getByText("WEG Linhares")).toBeTruthy();
    expect(screen.getByText("Quantidades")).toBeTruthy();
    expect(screen.getByText("Como o saldo é coberto")).toBeTruthy();
    expect(screen.getByText("11286701001")).toBeTruthy();
    expect(screen.getByText("Corte previsto para o turno da manhã.")).toBeTruthy();
    expect(screen.getAllByText("0,026").length).toBeGreaterThan(0);
  });

  it("mantém cada observação ligada à OP correta e omite observações vazias", () => {
    render(
      <DemandDetailModal
        line={{
          ...DEMAND,
          covering_orders: [
            ...DEMAND.covering_orders,
            {
              production_order: "OP-B",
              quantity: 0.01,
              expected_date: null,
              observation: "Separar no segundo turno.",
            },
            {
              production_order: "OP-C",
              quantity: 0.005,
              expected_date: null,
              observation: "",
            },
          ],
        }}
        branch="02"
        onClose={() => undefined}
      />,
    );
    const ops = document.querySelectorAll(".ppc-demand-line__op");
    expect(ops).toHaveLength(3);
    expect(within(ops[0] as HTMLElement).getByText("Corte previsto para o turno da manhã.")).toBeTruthy();
    expect(within(ops[1] as HTMLElement).getByText("Separar no segundo turno.")).toBeTruthy();
    expect(within(ops[2] as HTMLElement).queryByText("Observação da OP")).toBeNull();
  });

  it("expande e recolhe observações longas sem perder o conteúdo", () => {
    const note = "Programar na próxima janela; ".repeat(12);
    render(
      <DemandDetailModal
        line={{
          ...DEMAND,
          covering_orders: [{ ...DEMAND.covering_orders[0], observation: note }],
        }}
        branch="02"
        onClose={() => undefined}
      />,
    );
    const toggle = screen.getByRole("button", { name: "Ler observação completa" });
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(toggle);
    const expanded = screen.getByRole("button", { name: "Recolher observação" });
    expect(expanded.getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByText(note.trim())).toBeTruthy();
    fireEvent.click(expanded);
    expect(screen.getByRole("button", { name: "Ler observação completa" })).toBeTruthy();
  });

  it("apresenta alerta de cobertura parcial e estado vazio sem OP", () => {
    render(
      <DemandDetailModal
        line={{
          ...DEMAND,
          covering_orders: [],
          covered_by_orders: 0,
          uncovered_quantity: 0.026,
          op_coverage_incomplete: true,
        }}
        branch="02"
        onClose={() => undefined}
      />,
    );
    expect(screen.getByText("Nenhuma OP aberta alocada a este saldo.")).toBeTruthy();
    expect(screen.getByRole("status").textContent).toContain("cobertura exibida pode estar incompleta");
  });

  it("preserva fechamento e acesso à carga-máquina", () => {
    const close = vi.fn();
    render(<DemandDetailModal line={DEMAND} branch="02" onClose={close} />);
    expect(screen.getByRole("button", { name: "Abrir na carga máquina" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Fechar" }));
    expect(close).toHaveBeenCalledTimes(1);
  });

  it("não renderiza para demanda não selecionada", () => {
    const { container } = render(
      <DemandDetailModal line={null} branch="02" onClose={() => undefined} />,
    );
    expect(container.innerHTML).toBe("");
  });
});
