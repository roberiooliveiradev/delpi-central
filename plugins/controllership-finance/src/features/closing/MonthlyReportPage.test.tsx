import {
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const settlementsSpy = vi.fn();
const stockSpy = vi.fn();

vi.mock("./FinancialSettlementsPage", () => ({
  FinancialSettlementsPage: (props: {
    reportContext?: { period: string };
  }) => {
    settlementsSpy(props);
    return <div>Baixas financeiras — contexto {props.reportContext?.period}</div>;
  },
}));

vi.mock("./StockInventoryPage", () => ({
  StockInventoryPage: (props: {
    reportContext?: { period: string };
  }) => {
    stockSpy(props);
    return <div>Estoque — contexto {props.reportContext?.period}</div>;
  },
}));

import { MonthlyReportPage } from "./MonthlyReportPage";

afterEach(() => {
  cleanup();
  settlementsSpy.mockClear();
  stockSpy.mockClear();
});

describe("MonthlyReportPage — dispatcher contextual (UX-011)", () => {
  it("financial-settlements renderiza a página de Baixas com a competência da rota", () => {
    render(
      <MonthlyReportPage
        period="2026-10"
        reportKey="financial-settlements"
        onBack={vi.fn()}
      />,
    );

    expect(
      screen.getByText("Baixas financeiras — contexto 2026-10"),
    ).toBeTruthy();
    expect(settlementsSpy).toHaveBeenCalledWith(
      expect.objectContaining({ reportContext: { period: "2026-10" } }),
    );
    expect(stockSpy).not.toHaveBeenCalled();
  });

  it("stock-inventory renderiza a página de Estoque com a competência da rota", () => {
    render(
      <MonthlyReportPage
        period="2026-10"
        reportKey="stock-inventory"
        onBack={vi.fn()}
      />,
    );

    expect(screen.getByText("Estoque — contexto 2026-10")).toBeTruthy();
    expect(stockSpy).toHaveBeenCalledWith(
      expect.objectContaining({ reportContext: { period: "2026-10" } }),
    );
    expect(settlementsSpy).not.toHaveBeenCalled();
  });

  it("voltar restaura a aba Relatórios e divergências", () => {
    const onBack = vi.fn();
    render(
      <MonthlyReportPage
        period="2026-10"
        reportKey="financial-settlements"
        onBack={onBack}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: /Voltar para Relatórios e divergências/,
      }),
    );
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("chave desconhecida é estado honesto, não página vazia inventada", () => {
    render(
      <MonthlyReportPage
        period="2026-10"
        reportKey="relatorio-x"
        onBack={vi.fn()}
      />,
    );

    expect(
      screen.getByText(/ainda não possui uma página contextual/),
    ).toBeTruthy();
    expect(settlementsSpy).not.toHaveBeenCalled();
    expect(stockSpy).not.toHaveBeenCalled();
  });
});
