import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const getMock = vi.fn();

vi.mock("../../api/stockInventoryApi", () => ({
  getStockInventory: (...args: unknown[]) => getMock(...args),
}));

import { ApiError } from "../../api/httpClient";
import { StockInventoryPage } from "./StockInventoryPage";

const ITEM = {
  productCode: "P0001",
  description: "Produto Exemplo",
  productType: "MP",
  productGroup: "1000",
  unit: "KG",
  warehouse: "01",
  branchCode: "02",
  historicalQuantity: "10.0000",
  historicalStockValue: "100.5000",
};

function payload(overrides: Record<string, unknown> = {}) {
  return {
    report: "stock-inventory",
    period: "2026-09",
    referenceDate: "2026-09-30",
    dataAsOf: "2026-09-30",
    branchCode: "all",
    reportScope: "all_products",
    source: "protheus_sb9_sb1",
    officialP7: false,
    parityStatus: "TEST_NOT_RUN",
    status: "available",
    branchesAvailable: ["02"],
    branchesMissing: [],
    historicalTotal: "10576487.8400",
    pagination: {
      page: 1,
      page_size: 50,
      total_items: 1,
      total_pages: 1,
      has_next: false,
      has_previous: false,
    },
    items: [ITEM],
    summariesByType: [
      {
        productType: "MP",
        itemCount: 1,
        totalQuantity: "10.0000",
        totalStockValue: "100.5000",
      },
    ],
    summariesByWarehouse: [
      {
        branchCode: "02",
        warehouse: "01",
        itemCount: 1,
        totalQuantity: "10.0000",
        totalStockValue: "100.5000",
      },
    ],
    ...overrides,
  };
}

function fillPeriodAndSubmit() {
  const periodInput = screen.getByLabelText("Competência");
  fireEvent.change(periodInput, { target: { value: "2026-09" } });
  fireEvent.click(screen.getByRole("button", { name: "Consultar" }));
}

afterEach(() => {
  cleanup();
  getMock.mockReset();
});

describe("StockInventoryPage", () => {
  it("renderiza cabeçalho, disclaimer não-oficial e filtros", () => {
    render(<StockInventoryPage />);
    expect(screen.getByText("Estoque histórico — P7")).toBeTruthy();
    expect(
      screen.getByText(/não equivalem ao relatório oficial MATR460/i),
    ).toBeTruthy();
    expect(screen.getByLabelText("Competência")).toBeTruthy();
    expect(getMock).not.toHaveBeenCalled();
  });

  it("consulta envia period, branch, scope e paginação", async () => {
    getMock.mockResolvedValue(payload());
    render(<StockInventoryPage />);
    fillPeriodAndSubmit();
    await waitFor(() => expect(getMock).toHaveBeenCalled());
    const query = getMock.mock.calls[0][0];
    expect(query.period).toBe("2026-09");
    expect(query.branch).toBe("all");
    expect(query.reportScope).toBe("all_products");
    expect(query.page).toBe(1);
    expect(query.pageSize).toBe(50);
    await waitFor(() => screen.getByText("Produto Exemplo"));
  });

  it("filial é filtro de dados — encaminha o código selecionado", async () => {
    getMock.mockResolvedValue(payload());
    render(<StockInventoryPage />);
    const branchSelect = screen.getByLabelText("Filial");
    fireEvent.change(branchSelect, { target: { value: "02" } });
    fillPeriodAndSubmit();
    await waitFor(() => expect(getMock).toHaveBeenCalled());
    expect(getMock.mock.calls[0][0].branch).toBe("02");
  });

  it("mostra indicadores, resumos e tabela quando disponível", async () => {
    getMock.mockResolvedValue(payload());
    render(<StockInventoryPage />);
    fillPeriodAndSubmit();
    await waitFor(() => screen.getByText("Produto Exemplo"));
    expect(screen.getByText("Resumo por tipo de produto")).toBeTruthy();
    expect(screen.getByText("Resumo por armazém")).toBeTruthy();
    expect(screen.getByText("10.576.487,84")).toBeTruthy();
  });

  it("source_missing não exibe total nem zero", async () => {
    getMock.mockResolvedValue(
      payload({
        status: "source_missing",
        dataAsOf: null,
        branchesAvailable: [],
        branchesMissing: ["01"],
        historicalTotal: null,
        items: [],
        summariesByType: [],
        summariesByWarehouse: [],
        pagination: {
          page: 1,
          page_size: 50,
          total_items: 0,
          total_pages: 1,
          has_next: false,
          has_previous: false,
        },
      }),
    );
    render(<StockInventoryPage />);
    fillPeriodAndSubmit();
    await waitFor(() => screen.getByText("Snapshot não encontrado"));
    expect(screen.queryByText("Valor histórico total")).toBeNull();
  });

  it("incomplete sinaliza filial ausente", async () => {
    getMock.mockResolvedValue(
      payload({ status: "incomplete", branchesMissing: ["01"] }),
    );
    render(<StockInventoryPage />);
    fillPeriodAndSubmit();
    await waitFor(() =>
      screen.getByText("Dados parcialmente disponíveis"),
    );
  });

  it("erro 403 mostra estado de acesso restrito", async () => {
    getMock.mockRejectedValue(new ApiError(403, "Acesso negado."));
    render(<StockInventoryPage />);
    fillPeriodAndSubmit();
    await waitFor(() => screen.getByText("Acesso restrito"));
  });

  it("scope_unavailable mostra estado próprio", async () => {
    getMock.mockRejectedValue(
      new ApiError(403, "Escopo.", "scope_unavailable"),
    );
    render(<StockInventoryPage />);
    fillPeriodAndSubmit();
    await waitFor(() => screen.getByText("Escopo de dados indisponível"));
  });

  it("503 mostra dependência indisponível", async () => {
    getMock.mockRejectedValue(
      new ApiError(503, "Origem de dados financeiros indisponível."),
    );
    render(<StockInventoryPage />);
    fillPeriodAndSubmit();
    await waitFor(() => screen.getByText("Origem indisponível"));
  });
});
