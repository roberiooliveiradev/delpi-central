// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { LineFeederProductDetail } from "../types";
import { formatOpQuantity } from "../utils/formatOpQuantity";
import { LineFeederProductDetailModal } from "./LineFeederProductDetailModal";

vi.mock("./PpcConfirmModal", () => ({
  HostContainedWideDialog: ({
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
      <div>
        <h2>{title}</h2>
        <button type="button" onClick={onClose}>
          Fechar
        </button>
        {children}
      </div>
    ) : null,
}));

const DETAIL: LineFeederProductDetail = {
  branch: "01",
  cutoff: { at: "2026-09-22T14:00:00", date: "2026-09-22", time: "14:00" },
  product: {
    code: "50320064",
    description: "CHAPA",
    unit: "PC",
    pickup_location: "A-01",
  },
  work_centers: [
    {
      work_center: "CT-01",
      work_center_name: "BANCADA CT-01",
      required_qty: 10,
      to_deliver_qty: 0,
      status: "covered",
    },
  ],
  stock: { available: true, warehouse: "01", quantity: 250 },
  transfers: { available: true, items: [] },
};

afterEach(() => {
  cleanup();
});

describe("LineFeederProductDetailModal", () => {
  it("mostra visão geral com identidade e saldo do almoxarifado", () => {
    render(
      <LineFeederProductDetailModal
        open
        loading={false}
        error={null}
        detail={DETAIL}
        statuses={{ covered: { label: "Na bancada" } }}
        onClose={() => undefined}
      />,
    );
    expect(screen.getByText("Detalhes do material")).toBeTruthy();
    expect(screen.getAllByText("50320064").length).toBeGreaterThan(0);
    expect(screen.getAllByText("CHAPA").length).toBeGreaterThan(0);
    expect(screen.getByText("A-01")).toBeTruthy();
    expect(screen.getByText("Saldo no almoxarifado")).toBeTruthy();
    expect(screen.getByText(`${formatOpQuantity(250)} PC`)).toBeTruthy();
    expect(screen.getByText("Já na bancada")).toBeTruthy();
    expect(screen.queryByText("Nenhuma transferência recente para este produto.")).toBeNull();
  });

  it("abre bancadas e movimentações sem esconder o saldo na visão geral", () => {
    render(
      <LineFeederProductDetailModal
        open
        loading={false}
        error={null}
        detail={DETAIL}
        statuses={{ covered: { label: "Na bancada" } }}
        onClose={() => undefined}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Bancadas" }));
    expect(screen.getByText("BANCADA CT-01")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Movimentações" }));
    expect(screen.getByText("Nenhuma transferência recente para este produto.")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Visão geral" }));
    expect(screen.getByText("Saldo no almoxarifado")).toBeTruthy();
  });

  it("mostra saldo indisponível sem esconder o produto", () => {
    render(
      <LineFeederProductDetailModal
        open
        loading={false}
        error={null}
        detail={{
          ...DETAIL,
          stock: {
            available: false,
            warehouse: "01",
            quantity: null,
            message: "Não foi possível ler o saldo do almoxarifado agora.",
          },
        }}
        statuses={{}}
        onClose={() => undefined}
      />,
    );
    expect(screen.getAllByText("50320064").length).toBeGreaterThan(0);
    expect(screen.getByText("Não foi possível ler o saldo do almoxarifado agora.")).toBeTruthy();
  });

  it("alerta quando o almoxarifado não cobre a coleta", () => {
    render(
      <LineFeederProductDetailModal
        open
        loading={false}
        error={null}
        detail={{
          ...DETAIL,
          work_centers: [
            {
              ...DETAIL.work_centers[0],
              to_deliver_qty: 10,
              status: "at_risk",
            },
          ],
        }}
        statuses={{ at_risk: { label: "Em risco" } }}
        onClose={() => undefined}
      />,
    );
    expect(screen.getByText("Em risco")).toBeTruthy();
    expect(
      screen.getByText("O saldo do almoxarifado não cobre o que falta nas bancadas deste corte."),
    ).toBeTruthy();
  });

  it("fecha ao clicar em Fechar", () => {
    const onClose = vi.fn();
    render(
      <LineFeederProductDetailModal
        open
        loading={false}
        error={null}
        detail={DETAIL}
        statuses={{}}
        onClose={onClose}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Fechar" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("não renderiza quando fechado", () => {
    const { container } = render(
      <LineFeederProductDetailModal
        open={false}
        loading={false}
        error={null}
        detail={DETAIL}
        statuses={{}}
        onClose={() => undefined}
      />,
    );
    expect(container.innerHTML).toBe("");
  });
});
